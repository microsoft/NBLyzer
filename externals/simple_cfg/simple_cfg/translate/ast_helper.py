"""This module contains helper function.
Useful when working with the ast module."""

import ast
import logging
import os
import subprocess
from functools import lru_cache

from .transformer import CFGTransformer

log = logging.getLogger(__name__)
BLACK_LISTED_CALL_NAMES = ['self']

@lru_cache()
def generate_ast(code):
    try:
        tree = ast.parse(code)
        return CFGTransformer().visit(tree)
    except SyntaxError:
       raise SyntaxError('The ast module can not parse the file' 
                            ' and the python 2 to 3 conversion' 
                            ' also failed.')

def _get_call_names_helper(node):
    """Recursively finds all function names."""
    if isinstance(node, ast.Name):
        if node.id not in BLACK_LISTED_CALL_NAMES:
            yield node.id
            # For function id: 'np', get name of referenced variable (func attribute)
            if (node.id == 'np' and hasattr(node, 'id_attr')):
                if len(node.id_attr) > 0:
                    yield node.id_attr[0]
    elif isinstance(node, ast.Subscript):
        yield from _get_call_names_helper(node.value)
    elif isinstance(node, ast.Str):
        yield node.s
    elif isinstance(node, ast.Attribute):
        yield node.attr
        yield from _get_call_names_helper(node.value)

def get_call_names(node):
    """Get a list of call names."""
    return reversed(list(_get_call_names_helper(node)))


def _list_to_dotted_string(list_of_components):
    """Convert a list to a string seperated by a dot."""
    return '.'.join(list_of_components)


def get_call_names_as_string(node):
    """Get a list of call names as a string."""
    return _list_to_dotted_string(get_call_names(node))


class Arguments():
    """Represents arguments of a function."""

    def __init__(self, args):
        """Argument container class.

        Args:
            args(list(ast.args): The arguments in a function AST node.
        """
        self.args = args.args
        self.varargs = args.vararg
        self.kwarg = args.kwarg
        self.kwonlyargs = args.kwonlyargs
        self.defaults = args.defaults
        self.kw_defaults = args.kw_defaults

        self.arguments = list()
        if self.args:
            self.arguments.extend([x.arg for x in self.args])
        if self.varargs:
            self.arguments.extend(self.varargs.arg)
        if self.kwarg:
            self.arguments.extend(self.kwarg.arg)
        if self.kwonlyargs:
            self.arguments.extend([x.arg for x in self.kwonlyargs])

    def __getitem__(self, key):
        return self.arguments.__getitem__(key)

    def __len__(self):
        return self.args.__len__()
