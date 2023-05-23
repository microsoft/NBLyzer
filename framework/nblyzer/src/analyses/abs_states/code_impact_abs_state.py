# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
import ast
from copy import deepcopy

from simple_cfg.cfg_nodes import EntryOrExitNode
from ....src.IR.intermediate_representations import IntermediateRepresentations
from .abs_state import AbstractState
from ..runner.analysis_results import ErrorInfo, ErrorType
from ast import Name, NodeVisitor, arguments

class CodeImpactAS(AbstractState):
    def __init__(self, impacted_variables: dict[str: int] = {}, K: int = 2):
        self.impacted_variables: dict[str, int] = deepcopy(impacted_variables)
        self.K: int = K

    def __eq__(self, other: CodeImpactAS) -> bool:
        return self.impacted_variables.keys() == other.impacted_variables.keys() and self.K == other.K

    def projection(self) -> set[str]:
        if not len(self.impacted_variables):
            return set()
        return self.impacted_variables.keys()

    def aug_join(self, other: CodeImpactAS):
        for var in other.impacted_variables.keys():
            if var in self.impacted_variables.keys():
                self.impacted_variables[var] = max(self.impacted_variables[var], other.impacted_variables[var])
            else:
                self.impacted_variables[var] = other.impacted_variables[var]
        self.K = max(self.K, other.K)
    
    def contains(self, other: CodeImpactAS) -> bool:
        return other.impacted_variables.keys() <= self.impacted_variables.keys()

    def condition(self, cell_IR: IntermediateRepresentations, node, errors) -> list:
        for var, level in self.impacted_variables.items():
            new_error = ErrorInfo(cell_IR.cell_id, node.line_number, var.split("_usage")[0], ErrorType.CRITICAL, "Variable uses outdated values.")
            if new_error not in errors and level >= self.K and not isinstance(node, EntryOrExitNode):
                if var in cell_IR.UDA.defined_vars.keys() and cell_IR.UDA.defined_vars[var] == new_error.line:
                    errors.append(new_error)

                elif len(var.split("_usage")) > 1 and var.split("_usage")[0] in cell_IR.UDA.def_use_chains.unbound_names:
                    errors.append(new_error)
        return errors

    def set_var_level(self, var: str, level: int):
        if var in self.impacted_variables:
            self.impacted_variables[var] = max(self.impacted_variables[var], level)
        else:
            self.impacted_variables[var] = level

    def __str__(self) -> str:        
        impacted_var_str: str = "("
        if not len(self.impacted_variables):
            return "K = " + str(self.K)
        for var, level in self.impacted_variables.items():
            impacted_var_str += f"{var} -> {level}, "
        return "Impacted variables: " + impacted_var_str[:-2] + "), K: " + str(self.K)
