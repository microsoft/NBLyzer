# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import defaultdict
from copy import deepcopy
from .IR.intermediate_representations import IntermediateRepresentations
from .nblyzer import NBLyzer
from .constants import *

def reindex_results(nblyzer: NBLyzer, updated_index: int, added = True):
    for result in nblyzer.results.values():
        for path_result in result.path_results:
            for error in path_result.error_infos:
                if added and error.cell_id >= updated_index:
                    error.cell_id += 1
                    path_result.path = [error.cell_id]
                if not added and error.cell_id > updated_index:
                    error.cell_id -= 1
                    path_result.path = [error.cell_id]

class Event:
    def execute(self):
        pass

class AddActiveAnalysesEvent(Event):
    def __init__(self, active_analyses):
        self.active_analyses = active_analyses

    def execute(self, nblyzer):
        nblyzer.add_analyses(self.active_analyses)
        return nblyzer.run_analyses(-1, [IDLE, ISOLATED]).join_by_cell_id()

class OpenNotebookEvent(Event):
    def __init__(self, notebook_json):
        self.notebook_json = notebook_json

    def execute(self, nblyzer):
        nblyzer.load_notebook(self.notebook_json)

class RunCellEvent(Event):
    def __init__(self, cell_index):
        self.cell_index = cell_index

    def execute(self, nblyzer):
        results = nblyzer.run_analyses(self.cell_index, [STALE, DATA_LEAK])
        nblyzer.update_abstract_states(self.cell_index)
        nblyzer.notebook_IR[self.cell_index].last_ran_code = nblyzer.notebook_IR[self.cell_index].cell_code
        return results.join_by_cell_id()

class RunBatchEvent(Event):
    def __init__(self, start_cell):
        self.start_cell = start_cell

    def execute(self, nblyzer):
        return nblyzer.run_analyses(self.start_cell, detailed = True)
    
class AddCellEvent(Event):
    def __init__(self, position: int, kind: int, content: str) -> None:
        self.position: int = int(position)
        self.kind = int(kind)
        self.content = str(content)

    def execute(self, nblyzer: NBLyzer):
        new_notebook_IR: dict[int, IntermediateRepresentations] = defaultdict()
        all_keys = list(nblyzer.notebook_IR.keys())
        max_key = max(all_keys)
        for i in range(len(all_keys)):
            if all_keys[i] >= self.position:
                new_notebook_IR[all_keys[i] + 1] = nblyzer.notebook_IR[all_keys[i]]
                new_notebook_IR[all_keys[i] + 1].cell_id = all_keys[i] + 1
            if all_keys[i] < self.position:
                new_notebook_IR[all_keys[i]] = nblyzer.notebook_IR[all_keys[i]]
        
        if self.position <= max_key:
            new_notebook_IR[max_key + 1] = nblyzer.notebook_IR[max_key]
            new_notebook_IR[max_key + 1].cell_id = max_key + 1
        
        if self.kind == 2:
            new_notebook_IR[self.position] = IntermediateRepresentations(self.content, self.position)
        nblyzer.notebook_IR = new_notebook_IR
        reindex_results(nblyzer, self.position)
        return nblyzer.run_analyses(-1, [IDLE, ISOLATED]).join_by_cell_id()

class RemoveCellEvent(Event):
    def __init__(self, position: int) -> None:
        self.position: int = position

    def execute(self, nblyzer: NBLyzer):
        new_notebook_IR: dict[int, IntermediateRepresentations] = defaultdict()
        for index in nblyzer.notebook_IR.keys():
            if index > self.position:
                new_notebook_IR[index - 1] = nblyzer.notebook_IR[index]
                new_notebook_IR[index - 1].cell_id = index - 1
            if index < self.position:
                new_notebook_IR[index] = nblyzer.notebook_IR[index]
        
        nblyzer.notebook_IR = deepcopy(new_notebook_IR)
        reindex_results(nblyzer, self.position, False)
        return nblyzer.run_analyses(-1, [IDLE, ISOLATED]).join_by_cell_id()

class ChangeCellCodeEvent(Event):
    def __init__(self, new_code: str, cell_index: int, with_result: bool) -> None:
        self.new_code: str = new_code
        self.cell_index: int = cell_index
        self.with_result: bool = with_result

    def execute(self, nblyzer: NBLyzer):
        if self.cell_index in nblyzer.notebook_IR.keys():
            last_ran_code = nblyzer.notebook_IR[self.cell_index].last_ran_code
            nblyzer.notebook_IR[self.cell_index] = IntermediateRepresentations(self.new_code, self.cell_index, last_ran_code)
        if self.with_result:
            return nblyzer.run_analyses(-1, [IDLE, ISOLATED]).join_by_cell_id()
        
class CloseNotebookEvent(Event):
    def execute(self, nblyzer):
        nblyzer.reset()