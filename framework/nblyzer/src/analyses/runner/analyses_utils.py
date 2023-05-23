# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import defaultdict
from copy import deepcopy
import re
import ast

from simple_cfg.cfg_factory import CFG
from simple_cfg.cfg_nodes import AssignmentNode, EntryOrExitNode

def find_changed_vars(changed_cell_IR: CFG, old_cell_IR:CFG):
    changed_vars = set()
    for node in changed_cell_IR.CFG.nodes:
        if isinstance(node.ast_node, ast.Assign):
            found_pair = False
            for ref_node in old_cell_IR.CFG.nodes:
                if not isinstance(ref_node, EntryOrExitNode) and ast.dump(node.ast_node) == ast.dump(ref_node.ast_node):
                    found_pair = True
            if not found_pair:
                if isinstance(node.ast_node.targets, ast.Name) and node.ast_node.targets.id.find("__chain_tmp") == -1:
                    changed_vars.add(node.ast_node.targets.id)
                elif isinstance(node.ast_node.targets, ast.Subscript) and node.ast_node.targets.value.id.find("__chain_tmp") == -1:
                    changed_vars.add(node.ast_node.targets.value.id)
                else:
                    for target in node.ast_node.targets:
                        if isinstance(target, ast.Name) and target.id.find("__chain_tmp") == -1:
                            changed_vars.add(target.id)
                        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id.find("__chain_tmp") == -1:
                            changed_vars.add(target.value.id)
                        else:
                            for t in ast.walk(target):
                                if isinstance(t, ast.Name) and t.id.find("__chain_tmp") == -1:
                                    changed_vars.add(t.id)                            
    return changed_vars

def get_all_unbound_vars(notebook_IR):
    unbound_vars = set()
    for data in notebook_IR.values():
        unbound_vars.update(data.UDA.def_use_chains.unbound_names)
    return unbound_vars

class AssignParserVisitor(ast.NodeVisitor):
    def __init__(self):
        self.def_variables = set[str]()
        self.assigned_variables = set[str]()
    
    def visit_Name(self, node: ast.Name):
        if node.id.find("__chain_tmp") == -1:
            self.assigned_variables.add(node.id)

    def visit_arguments(self, node: ast.arguments) -> None:
        if isinstance(node, ast.Name) and node.id.find("__chain_tmp") == -1:
            self.assigned_variables.add(node.id)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        for n in ast.walk(node.value):
            if isinstance(n, ast.Name) and n.id.find("__chain_tmp") == -1:
                self.assigned_variables.add(n.id)

    def visit_Call(self, node: ast.Call) -> None:
        for n in ast.walk(node.func):
            if isinstance(n, ast.Name) and n.id.find("__chain_tmp") == -1:
                self.assigned_variables.add(n.id)
        for arg in node.args:
            self.visit(arg)

    def parse_target(self, node):
        if isinstance(node, ast.Name) and node.id.find("__chain_tmp") == -1:
            self.def_variables.add(node.id)
        elif isinstance(node, ast.Call):
            for n in ast.walk(node.func):
                if isinstance(n, ast.Name) and n.id.find("__chain_tmp") == -1:
                    self.def_variables.add(n.id)
        elif isinstance(node, ast.Attribute):
            for n in ast.walk(node.value):
                if isinstance(n, ast.Name) and n.id.find("__chain_tmp") == -1:
                    self.def_variables.add(n.id)
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name) and node.value.id.find("__chain_tmp") == -1:
                self.def_variables.add(node.value.id)
            elif isinstance(node.value, ast.Attribute):
                for n in ast.walk(node.value):
                    if isinstance(n, ast.Name) and n.id.find("__chain_tmp") == -1:
                        self.def_variables.add(n.id)   
        elif isinstance(node, ast.List) or isinstance(node, ast.Tuple):
                for element in node.elts:
                    for n in ast.walk(element):
                        if isinstance(n, ast.Name):
                            self.def_variables.add(n.id)   

    def parse_assign(self, node):
        if isinstance(node, ast.Assign):
            if isinstance(node.targets, list):
                for target in node.targets:
                    self.parse_target(target)
            else:
                self.parse_target(node.targets)

            self.visit(node.value)
