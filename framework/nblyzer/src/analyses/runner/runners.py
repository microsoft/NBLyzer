# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from copy import deepcopy
from unittest import result
from ..abs_states.abs_state import AbstractState
from .analysis_results import PathResult, Result, ErrorType
from ..analysis import Analysis

from simple_cfg.cfg_factory import CFG
from simple_cfg.cfg_nodes import Node
from collections import defaultdict

from ....src.IR.intermediate_representations import IntermediateRepresentations
from .queue import FifoQueue

class Runner:
    def __init__(self, stats, cell_state_map: dict[int, AbstractState], cells_summary_map: dict[int, IntermediateRepresentations]):
        self.stats = stats
        self.cell_state_map: dict[int, AbstractState] = deepcopy(cell_state_map)
        self.error_states: list[AbstractState] = list()
        self.cells_summary_map: dict[int, IntermediateRepresentations] = cells_summary_map
    
    def intra_fixpoint_runner(self, cell_IR: IntermediateRepresentations, analysis: Analysis, as_init: AbstractState, K = None, imports = set()):
        cfg: CFG = cell_IR.CFG
        node_state_map = defaultdict(type(as_init))
        transform_order: FifoQueue = FifoQueue()
        transform_order.populate(cfg.nodes[0].outgoing)
        errors = []
        as_entry = deepcopy(as_init)

        while not transform_order.empty():
            next_node: Node = transform_order.pop()
            states_of_ingoing = self.get_states_of_ingoing(next_node.ingoing, node_state_map)

            if cfg.nodes[0] in next_node.ingoing:
                states_of_ingoing.append(as_entry)
            as_entry = analysis.combine_states(states_of_ingoing)

            as_transformed: AbstractState = analysis.F_transformer(next_node, as_entry, cell_IR)
            as_transformed.condition(cell_IR, next_node, errors)

            as_prev = node_state_map[next_node]
        
            if as_prev != as_transformed:
                for node in next_node.outgoing:
                    transform_order.push(node)
                node_state_map[next_node] = as_transformed
            
            for err in errors:
                if err.error_type == ErrorType.TERMINAL:
                    return as_transformed, errors

        cell_post_state = node_state_map[cfg.nodes[-1]]
        return cell_post_state, errors

    def get_states_of_ingoing(self, nodes, node_state_map) -> list[AbstractState]:
        return [node_state_map[node] for node in nodes if node in node_state_map]

    def inter_fixpoint_runner(self, analysis: Analysis, cell_id, abstract_state: AbstractState, K, cpath=[], results: Result = Result()):
        assert(cell_id is not None)
        swap = None
        if K:
            abstract_state_pre = abstract_state
            abstract_state, errors = self.intra_fixpoint_runner(self.cells_summary_map[cell_id], analysis, abstract_state_pre, len(cpath))
            if cell_id in self.cell_state_map and abstract_state.contains(abstract_state_pre): 
                self.stats.log_fp(len(cpath))
                return results

            cpath.append(cell_id)

            if errors != []:
                for err in errors:
                    path_result: PathResult = PathResult(cpath, errors)
                    if path_result not in results.path_results:
                        results.add_path_results([path_result])
                        self.error_states += [abstract_state]
                        if err.error_type == ErrorType.TERMINAL:
                            return results
            swap = deepcopy(self.cell_state_map[cell_id]) if cell_id in self.cell_state_map else None
            self.cell_state_map[cell_id] = abstract_state
            for c in self.cells_summary_map.keys():
                if c != cell_id:
                    pre_summary = analysis.calculate_pre(self.cells_summary_map[c])
                    if bool(pre_summary) and c in analysis.necessary and analysis.phi_condition(abstract_state.projection(), pre_summary, self.cells_summary_map[cell_id]):
                        self.stats.log_phi(True)
                        results = self.inter_fixpoint_runner(analysis, c, abstract_state, K - 1, deepcopy(cpath), results)
                    else:
                        self.stats.log_phi(False)

            if swap:
                self.cell_state_map[cell_id] = swap
            else:
                self.cell_state_map.pop(cell_id)

        return results
