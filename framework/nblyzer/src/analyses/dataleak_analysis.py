# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import defaultdict
from simple_cfg.cfg_nodes import AssignmentCallNode, AssignmentNode, BBorBInode, RestoreNode
from .abs_states.dataleak_abs_state import (
    DataLeakAbstractDomain,
    DataLeakAbstractState,
    DataFrameSet,
    Usage
)
from .abs_domains.dataleak_lattice.data_frame import DataFrame, Rows, Columns
from ..IR.intermediate_representations import IntermediateRepresentations
from .runner.analysis_results import Result, ErrorType
from .runner.runners import Runner
from .runner.stats import Stats

import ast
import copy
from .analysis import Analysis

class DataLeakAnalysis(Analysis):
    def __init__(self):
        super().__init__()
        self.resetKB = {'read_csv', 'genfromtxt'}
        self.taintKB = {'normalize', 'fit_transform'}
        self.trainKB = {'fit', 'train'}
        self.testKB = {'predict'}
        self.splitKB = {'train_test_split'}
        self.dropKB = {'drop'}
        self.tts_count = 0
        self.necessary = set[int]()
        self.abstract_state = DataLeakAbstractState()


    def F_transformer(self, cfg_node, a_state: DataLeakAbstractState, cell_IR):
        '''
        Gluing function for various construct transformers. 
        '''
        if isinstance(cfg_node, RestoreNode):
            other: DataLeakAbstractDomain = a_state.state[cfg_node.right_hand_side[0]]
            a_state.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(copy.deepcopy(other.dfs), other.taint, other.usages.copy(), dull=other.dull)

        if not cfg_node.ast_node:
            return a_state

        # as_transformed: DataLeakAbstractState = copy.deepcopy(a_state)
        as_transformed = a_state

        if isinstance(cfg_node, AssignmentCallNode):
            '''
            Renames intermediate call nodes and transfers them to variables
            '''
            lhs, rhs = cfg_node.left_hand_side, cfg_node.right_hand_side[0]

            if rhs not in as_transformed.state:
                return as_transformed

            as_transformed.state[lhs] = as_transformed.state[rhs]
            as_transformed.state.pop(rhs)

            return as_transformed

        if isinstance(cfg_node, BBorBInode):
            '''
            Black-box or Built-in functions include majority of data science library functions.
            '''
            func_name = self._extract_func(cfg_node)

            if func_name in self.splitKB:
                self.split_transformer(cfg_node, as_transformed)

            elif func_name in self.dropKB:
                self.drop_transformer(cfg_node, as_transformed)
                
            elif func_name in self.resetKB:
                self.reset_transformer(cfg_node, as_transformed)

            elif func_name in self.taintKB:
                self.taint_transformer(cfg_node, as_transformed)

            elif func_name in self.trainKB:
                # Should be visitor ideally.
                x_kw = self._extract_kw(cfg_node, 'x')
                x = x_kw[0].value.id if x_kw else None
                self._clone_assign(as_transformed, cfg_node, override_source=x).usages.add(Usage.TRAIN)

            elif func_name in self.testKB:
                self._clone_assign(as_transformed, cfg_node).usages.add(Usage.TEST)

            else:
                # All other function calls not related to Data Leak.
                as_transformed.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(dull=True)

            return as_transformed

        if isinstance(cfg_node, AssignmentNode):

            if isinstance(cfg_node.ast_node.value, ast.Name):
                '''
                Plain variable to variable assignment.
                '''
                self._clone_assign(as_transformed, cfg_node, override_source=cfg_node.ast_node.value.id)

            elif isinstance(cfg_node.ast_node.value, ast.Subscript):

                if isinstance(cfg_node.ast_node.value.value, ast.Attribute) and isinstance(cfg_node.ast_node.value.value.value, ast.Name):
                    self.iloc_transformer(cfg_node, as_transformed)

                elif isinstance(cfg_node.ast_node.value.value, ast.Name):
                    self.slice_transformer(cfg_node, as_transformed)

            else:
                as_transformed.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(dull=True)

            return as_transformed

        return as_transformed


    def split_transformer(self, cfg_node, as_transformed):
        '''
        Dealing with train_test_split return values. For simplicity, always truncate based on test size.
        Go over train_test_split return values, and regardless of their linkage to two first arguments,
        perform splitting. After all 4 have been grabbed, counter is reset.
        '''
        test_size_kw, train_size_kw = self._extract_kw(cfg_node, 'test_size'), self._extract_kw(cfg_node, 'train_size')
        train_size = train_size_kw[0].value.value if (train_size_kw and isinstance(train_size_kw[0].value, ast.Constant)) else None
        test_size = test_size_kw[0].value.value if (test_size_kw and isinstance(test_size_kw[0].value, ast.Constant)) else (0.25 if not train_size else None)

        test_size = round(1.0 - train_size, 4) if not test_size else test_size
        
        arg_pos = 1 if self.tts_count == 2 or self.tts_count == 3 else 0
        invert_trunc = self.tts_count == 1 or self.tts_count == 3

        self._clone_assign(as_transformed, cfg_node, arg_pos= arg_pos)
        as_transformed.state[cfg_node.left_hand_side].dfs.truncate_rows(test_size, inverse=invert_trunc)

        self.tts_count = self.tts_count + 1 if self.tts_count < 3 else 0


    def drop_transformer(self, cfg_node, as_transformed):
        convert = {'columns': 1, 'rows' : 1}
        axis_kw, columns_kw = self._extract_kw(cfg_node, 'axis'), self._extract_kw(cfg_node, 'columns')
        index_kw, labels_kw = self._extract_kw(cfg_node, 'index'), self._extract_kw(cfg_node, 'labels')

        if columns_kw:
            args, axis = columns_kw[0].value, 1

        elif index_kw: 
            args, axis =  index_kw[0].value, 0

        else:                
            args = labels_kw[0].value if labels_kw else cfg_node.ast_node.args[0]
            if axis_kw:
                axis = axis_kw[0].value.value
            elif len(cfg_node.ast_node.args) >= 2:
                axis = cfg_node.ast_node.args[1].value
            else:
                axis = 0
                
        if isinstance(args, ast.Attribute) or isinstance(args, ast.Name) or (isinstance(args, ast.List) and isinstance(args.elts[0], ast.Name)):
            '''
            Column arrays taken as an ast.Name. Requires another analysis to be tracked.
            '''
            return
            
        self._clone_assign(as_transformed, cfg_node, override_source=cfg_node.ast_node.func.value.id)
        axis = convert[axis] if isinstance(axis, str) else axis
        
        
        if isinstance(args, ast.List):
            if axis == 0 and args.elts and isinstance(args.elts[0].value, str):
                return
            for arg in args.elts:
                self._invoke_drop(arg.value, axis, as_transformed.state[cfg_node.left_hand_side])
        else:
            if axis == 0 and isinstance(args.value, str):
                return
            self._invoke_drop(args.value, axis, as_transformed.state[cfg_node.left_hand_side])


    def reset_transformer(self, cfg_node, as_transformed):
        '''
        If argument is local directory plus file name track only the file name.
        '''
        source_arg = self._extract_filename(cfg_node)
        
        df = DataFrame(source_arg, Columns(all=True), Rows())
        dfs = DataFrameSet({source_arg: [df]})

        as_transformed.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(dfs, False, set[Usage]())


    def taint_transformer(self, cfg_node, as_transformed):
        '''
        Handles of variations of an argument (first positional).
        E.g. plain dataset name, attribute like df.values etc...
        '''
        x_kw = self._extract_kw(cfg_node, 'X')
        arg = x_kw[0].value.id if x_kw else cfg_node.ast_node.args[0]

        if isinstance(arg, ast.Name):
            new_source = arg.id

        elif isinstance(arg, ast.Subscript):
            new_source = arg.value.value.id if isinstance(arg.value, ast.Attribute) else arg.value.id
            
        elif isinstance(arg, ast.Call):
            '''
            Temporary
            '''
            if isinstance(arg.func.value, ast.Name):
                new_source = arg.func.value.id
            else:
                new_source = arg.func.value.value.value.id
        
        elif isinstance(arg, ast.Attribute):
            new_source = arg.value.id
                
            
        self._clone_assign(as_transformed, cfg_node, override_source= new_source).apply_taint(new_source= new_source)


    def iloc_transformer(self, cfg_node, as_transformed):
        '''
        'Iloc-ed' variable to variable assignment.
        '''
        to_slice: DataLeakAbstractDomain = self._clone_assign(as_transformed, cfg_node, override_source=cfg_node.ast_node.value.value.value.id)
        slice = cfg_node.ast_node.value.slice

        if not isinstance(slice, ast.Slice) or self._incalculable(slice):
            return
            
        lw, up = self._get_if_int(slice.lower), self._get_if_int(slice.upper)                        
        to_slice.dfs.slice_rows(lw, up)


    def slice_transformer(self, cfg_node, as_transformed):
        '''
        Handles all variations of slicing. Row picking by ranges or column picking by names.
        '''
        to_slice: DataLeakAbstractDomain = self._clone_assign(as_transformed, cfg_node, override_source=cfg_node.ast_node.value.value.id)

        slice = cfg_node.ast_node.value.slice

        columns = list[str]()
        if isinstance(slice, ast.List):
            columns = {const.value : True for const in slice.elts}

        elif isinstance(slice, ast.Constant):
            columns = {slice.value: True}

        elif isinstance(slice, ast.Slice) and not self._incalculable(slice):
            '''
            ast.Slice -> Picks rows from certain range.
            '''

            lw, up = self._get_if_int(slice.lower), self._get_if_int(slice.upper)             
            to_slice.dfs.slice_rows(lw, up)

            return        

        else:
            '''
            Other possibilities for a slice field:
            
            ast.Compare -> Picks rows with certain numerical values. Statically cannot be calculated.
            Takes the worst case scenario, all rows.

            ast.Name -> Picks columns from provided list(named).
            Discuss implementing column only tracking system for precision improvement.
            '''    
            return

        to_slice.dfs.pick_columns(columns)


    def _extract_func(self, cfg_node):
        '''
        Extracts function name depending on its invocation form: as plain name or attribute of other name.
        '''
        func = cfg_node.ast_node.func
        return func.id if isinstance(cfg_node.ast_node.func, ast.Name) else func.attr 


    def _extract_kw(self, cfg_node, name):
        return list(filter(lambda kw: kw.arg == name, cfg_node.ast_node.keywords))


    def _extract_filename(self, cfg_node):
        if isinstance(cfg_node.ast_node.args[0], ast.BinOp):
            return cfg_node.ast_node.args[0].right.value

        elif isinstance(cfg_node.ast_node.args[0], ast.Constant):
            return cfg_node.ast_node.args[0].value
    
        else:
            # Consume the whole node as a source for now.
            return ast.dump(cfg_node.ast_node.args[0])  

    def _invoke_drop(self, value, axis, domain : DataLeakAbstractDomain) -> None:
        '''
        Drop wrapper for readability.
        '''
        if axis == 1:
            domain.dfs.drop_columns(value)
        else:
            domain.dfs.drop_rows(int(value))

    def _get_if_int(self, node):
        '''
        Covers situations where negative numbers are represented with ast.UnaryOp enveloping ast.Constant.
        Returns None if illegal.
        '''
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.UnaryOp):
            return - node.operand.value
        return None

    def _incalculable(self, slice: ast.Slice):
        return (slice.lower != None and not self._get_if_int(slice.lower)) or (slice.upper != None and not self._get_if_int(slice.upper))

    def _clone_assign(self,as_transformed: DataLeakAbstractState, cfg_node, override_source=None, arg_pos=0) -> DataLeakAbstractDomain:
        '''
        Helper function that extracts source and lhs from cfg node and performs needed deepcopy and assignment.
        '''
        if override_source:
            source_arg = override_source

        else:
            '''
            Default way of source extraction.
            Try to handle in future: 
                Argument not data frame but function that returns one.
            '''
            if arg_pos >= len(cfg_node.ast_node.args) or not isinstance(cfg_node.ast_node.args[arg_pos], ast.Name):
                as_transformed.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(dull= True)
                return as_transformed.state[cfg_node.left_hand_side]

            source_arg = cfg_node.ast_node.args[arg_pos].id

        other: DataLeakAbstractDomain = as_transformed.state[source_arg]
        as_transformed.state[cfg_node.left_hand_side] = DataLeakAbstractDomain(copy.deepcopy(other.dfs), other.taint, other.usages.copy(), dull=other.dull)

        return as_transformed.state[cfg_node.left_hand_side]

    def phi_condition(self, current: set, pre: set, cell_IR: IntermediateRepresentations):
        return (pre <= current)

    def update_abstract_state(self, cell_IR, notebook_IR):
        self.abstract_state, _ = Runner(self.stats, defaultdict(DataLeakAbstractState), notebook_IR).intra_fixpoint_runner(cell_IR, self, self.abstract_state)

    def combine_states(self, states: list[DataLeakAbstractState]):
        if len(states) == 1:
            return states[0]

        res_state = DataLeakAbstractState()
        for s in states:
            res_state.aug_join(s)

        return res_state

    def find_necessary_cells(self, notebook_IR):

        dataleak_kb : set[str] = (self.testKB | self.trainKB)

        for cell, IR in notebook_IR.items():
            for node in IR.CFG.nodes:
                if isinstance(node, BBorBInode):
                    if self._extract_func(node) in dataleak_kb:
                        self.necessary.add(cell)
                        break

                elif isinstance(node, AssignmentNode):
                    '''
                    Covers both AssignmentCallNode and AssignmentNode
                    '''
                    self.necessary.add(cell)
                    break

    def analyze_notebook(self, notebook_IR, old_cell_IR = None, level = 4, filename=""):
        
        self.notebook_IR: dict[int, IntermediateRepresentations] = notebook_IR

        pre = notebook_IR[old_cell_IR.cell_id].UDA.def_use_chains.unbound_names - notebook_IR[old_cell_IR.cell_id].UDA.funcs
        if not self.phi_condition(self.abstract_state.projection(), pre, old_cell_IR):
            return Result()

        stat = Stats(old_cell_IR.cell_id, filename) 
        stat.log_start()

        result = Runner(stat, defaultdict(DataLeakAbstractState), notebook_IR).inter_fixpoint_runner(
            self,
            old_cell_IR.cell_id,
            abstract_state=self.abstract_state,
            K=level,
            cpath=[],
            results = Result()
        )

        stat.log_end()
        self.stats.append(stat)
        return result

    def summarize_result(self, result: Result) -> Result:
        summarized_result: Result = result.distinct_errors()
        for path_result in result.distinct_errors().path_results:
            for err in path_result.error_infos:
                if err.error_type == ErrorType.TERMINAL:
                    err.error_message += " Path that will lead to this: " + str(path_result.path)
        
        return summarized_result

    def calculate_pre(self, cell_IR):
        return cell_IR.UDA.unbound_final
