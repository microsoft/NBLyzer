# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import ABC
from .runner.analysis_results import Result

class Analysis(ABC):
    def __init__(self):
        self.abstract_state = None
        self.stats = []
        self.necessary: set[int] = set[int]()

    def analyze_notebook(self, notebook_IR, old_cell_IR, level, filename=""):
        pass

    def F_transformer(self, cfg_node, a_state, cell_IR):
        pass

    def update_abstract_state(self, cell_IR, notebook_IR):
        pass

    def combine_states(self, states):
        pass

    def phi_condition(self, current: set, pre: set, cell_IR):
        pass

    def calculate_pre(self, cell_IR):
        pass

    def summarize_result(self, result: Result) -> Result:
        return result

    def find_necessary_cells(self, notebook_IR) -> None:
        self.necessary = set(notebook_IR.keys())
