# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from ast import Assign, expr
import gast as ast

class AssignsVisitor(ast.NodeVisitor):
    def __init__(self, def_use_chains):
        self.def_use_chains = def_use_chains
        self.funcs = set()
        self.imports = set()
        self.defined_vars = dict()
        super().__init__()

    def visit_Import(self, node: ast.Import):
        for name in node.names:
            self.imports.add(name.asname if name.asname else name.name)        

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for name in node.names:
            self.imports.add(name.asname if name.asname else name.name)  

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                self.funcs.add(node.value.func.id)
    
    def _get_if_func(self, value):
        if isinstance(value, ast.Call):
            if isinstance(value.func, ast.Name):
                self.funcs.add(value.func.id)

    def visit_Assign(self, node: Assign):
        if isinstance(node.value, ast.BinOp):
            self._get_if_func(node.value.left)
            self._get_if_func(node.value.right)

        else:
            self._get_if_func(node.value)

        names = set()
        if isinstance(node.value, ast.Name):
            names.add(node.value.id)
        else:
            for name in ast.walk(node.value):
                if isinstance(name, ast.Name):
                    names.add(name.id)
        targets = list[expr]()
        if isinstance(node.targets, list):
            targets = node.targets
        else:
            targets = [node.targets]
        for target in targets:
            if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                self.defined_vars[target.id] = node.lineno
            
            elif isinstance(target, ast.List) or isinstance(target, ast.Tuple):
                for element in target.elts:
                    for target_node in ast.walk(element):
                        if isinstance(target_node, ast.Name) and isinstance(target_node.ctx, ast.Store):
                            self.defined_vars[target_node.id] = node.lineno
            
            elif isinstance(target, ast.Subscript) or isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and isinstance(target.value.ctx, ast.Store):
                    self.defined_vars[target.value.id] = node.lineno
                else:
                    for target_node in ast.walk(target.value):
                        if isinstance(target_node, ast.Name) and isinstance(target_node.ctx, ast.Store):
                            self.defined_vars[target_node.id] = node.lineno

    def combine(self):
        self.unbound_final = self.def_use_chains.unbound_names - (self.funcs | self.imports)
