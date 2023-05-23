# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
import ast
from simple_cfg.cfg_nodes import Node, AssignmentNode
from ....src.IR.intermediate_representations import IntermediateRepresentations
from .abs_state import AbstractState
from ..abs_domains.dataleak_lattice.data_frame_sets import DataFrameSet
from ..runner.analysis_results import ErrorInfo, ErrorType
from itertools import product
from enum import Enum, auto

class Usage(Enum):
    TRAIN = auto()
    TEST = auto()
    NONE = auto()

class DataLeakAbstractDomain:
    def __init__(self, dfs: DataFrameSet = DataFrameSet(), taint: bool = False, usages: set[Usage] = set[Usage](), dull=False) -> None:
        '''
        Abstract domain that keeps track of data frames, if those data frames are tainted,
        if any data frames have been used for testing or training
        '''
        self.dull = dull
        self.dfs: DataFrameSet = dfs
        self.taint: bool = taint
        self.usages: set[Usage] = usages

    def apply_taint(self, new_source: str) -> DataLeakAbstractDomain:
        self.taint = True
        self.dfs.rename_sources(new_source)
        return self

    def __eq__(self, other: DataLeakAbstractDomain) -> bool:
        if self.dull == other.dull:
            return True

        return self.dfs == other.dfs and self.taint == other.taint and self.usages == other.usages

    def __ne__(self, other: DataLeakAbstractDomain) -> bool:
        return not self == other

class DataLeakAbstractState(AbstractState):
    def __init__(self) -> None:
        '''
        Object that maps variables to corresponding Abstract Domain element.
        '''
        self.state: dict[str, DataLeakAbstractDomain] = dict()
        super().__init__()
        

    def __getitem__(self, key: str) -> DataLeakAbstractDomain:
        return self.state[key]

    def condition(self, cell_IR: IntermediateRepresentations, node: Node, errors: list[ErrorInfo]) -> list:        
        test_domain: list[DataLeakAbstractDomain] = [e for e in self.state.values() if Usage.TEST in e.usages]
        train_domain: list[DataLeakAbstractDomain] = [e for e in self.state.values() if Usage.TRAIN in e.usages]

        for test_dfs, train_dfs in product(test_domain, train_domain):
            if test_dfs.dfs.cartesian_overlap(train_dfs.dfs):
                if isinstance(node, AssignmentNode):
                    if isinstance(node.ast_node, ast.Call) and node.ast_node.args and isinstance(node.ast_node.args[0], ast.Name):
                        errors.append(ErrorInfo(cell_IR.cell_id, node.line_number, node.ast_node.args[0].id, ErrorType.TERMINAL, "Training model with data leak."))
                else:
                    errors.append(ErrorInfo(cell_IR.cell_id, node.line_number, node.label, ErrorType.TERMINAL, "Training model with data leak."))
                return errors
            
            if test_dfs.dfs.cartesian_overlap(train_dfs.dfs, weak=True) and test_dfs.taint and train_dfs.taint:
                if isinstance(node, AssignmentNode):
                    if isinstance(node.ast_node, ast.Call):
                        errors.append(ErrorInfo(cell_IR.cell_id, node.line_number, node.ast_node.args[0].id, ErrorType.TERMINAL, "Training model with data leak."))
                else:
                    errors.append(ErrorInfo(cell_IR.cell_id, node.line_number, node.label, ErrorType.TERMINAL, "Training model with data leak."))
                return errors
        return errors

    def aug_join(self, other: DataLeakAbstractState) -> DataLeakAbstractState:
        '''
        Augment join operation on two Abstract states.
        '''
        for other_var, other_domain in other.state.items():

            if other_var not in self.state:
                self.state[other_var] = other_domain
                continue

            self.state[other_var] = DataLeakAbstractDomain(
                self.state[other_var].dfs | other_domain.dfs,
                self.state[other_var].taint | other_domain.taint,
                self.state[other_var].usages.union(other_domain.usages),
                self.state[other_var].dull | other_domain.dull
            )

        return self

    def contains(self, other: DataLeakAbstractState) -> bool:
        self_filtered = {k:v for k, v in self.state.items() if k[0] != '~'}
        other_filtered = {k:v for k, v in other.state.items() if k[0] != '~'}
        return other_filtered.items() <= self_filtered.items() 

    def projection(self) -> set[str]:
        '''
        Get all variables that map to Data Frame Sets with non-empty rows.
        TODO: Resolve variable binding for ones that do not interfere with dataleak domain (currently solved with dull)
        '''
        return {var for var, dom in self.state.items() if dom.dfs.some_rows() or dom.dull}

    def __eq__(self, other: DataLeakAbstractState) -> bool:
        return self.state == other.state

    def __ne__(self, other: DataLeakAbstractState) -> bool:
        return not self == other
