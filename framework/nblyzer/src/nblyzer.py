# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from collections import defaultdict
from .analyses.dataleak_analysis import DataLeakAnalysis
from .analyses.stale_cell_analysis import StaleCellAnalysis
from .analyses.idle_cell_analysis import IdleCellAnalysis
from .analyses.isolated_cell_analysis import IsolatedCellAnalysis
from nblyzer.src.constants import *

from .IR.intermediate_representations import IntermediateRepresentations
from .analyses.runner.analysis_results import Result, PathResult, ErrorType, ErrorInfo

class NBLyzer():
    def __init__(self, level=5, filename=""):
        self.reset()
        self.all_analyses = {
            DATA_LEAK: DataLeakAnalysis(),
            STALE: StaleCellAnalysis(),
            IDLE: IdleCellAnalysis(),
            ISOLATED: IsolatedCellAnalysis()
        }
        self.level = level
        self.results: dict[str, Result] = defaultdict(Result)
        self.filename = filename

    def load_script(self, notebook_str):
        if not self.notebook_IR:
            self.notebook_IR = {}
            self.notebook_IR[0] = IntermediateRepresentations(notebook_str, 0)
        else:
            Exception("A script has already been loaded.")

    def load_notebook(self, notebook_json):
        '''
        Creates an Abstract Syntax Tree (AST) objects from a notebook in JSON format.

        Parameters
        ----------
        old_notebook_json: str
            A string in the format '[{cell_type: code, language: python, source: some code}, {...}, ...]

        Returns
        ----------
        notebook_IR: dict[int] = AST
            Dictionary where key is cell_id and value is AST of the code in the cell
        notebook_code: dict[int] = str
            Dictionary where key is cell_id and value is the code in the cell
        '''    
        self.results: dict[str, Result] = defaultdict(Result)
        if not self.notebook_IR:
            self.notebook_IR = {}
            if notebook_json:
                for cnt, cell in enumerate(notebook_json):
                    if (cell["cell_type"] != "code"):
                        continue
                    if isinstance(cell["source"], list):
                        cell["source"]  = "".join(cell["source"])

                    self.notebook_IR[cnt] = IntermediateRepresentations(cell["source"], cnt)
            else:
                Exception("A notebook has already been loaded.")

    def add_analyses(self, analyses):
        '''
        Add analyses to dict of active analyses.

        Parameters
        ----------
        analyses: list(str)
            A list of analyses to be added to active analyses.
        '''
        self.active_analyses = analyses


    def update_abstract_states(self, cell_index):
        for analysis in self.all_analyses.values():
            analysis.update_abstract_state(self.notebook_IR[cell_index], self.notebook_IR)

    def execute_event(self, event):
        return event.execute(self)

    def join_analyses_results(self):
        new_results: Result = Result()
        for analysis_str in self.active_analyses:
            new_results.join_results(self.results[analysis_str])
        return new_results

    def run_analyses(self, cell_index: int, analyses: list[str] = None, detailed: bool = False):
        if cell_index == -1:
            changed_cell_IR = None
        else:
            if (cell_index in self.notebook_IR):
                changed_cell_IR = IntermediateRepresentations(self.notebook_IR[cell_index].last_ran_code, cell_index)
            else:
                new_results: Result = Result()
                new_results.add_path_results([PathResult([cell_index], [ErrorInfo(cell_index, 0, "", ErrorType.CRITICAL, "Cannot start from cell with no code")])])
                return new_results
        if not analyses:
            analyses = self.active_analyses
        for analysis_str in analyses:
            if analysis_str in self.active_analyses:
                self.all_analyses[analysis_str].find_necessary_cells(self.notebook_IR)
                self.results[analysis_str] = self.all_analyses[analysis_str].analyze_notebook(self.notebook_IR, changed_cell_IR, self.level, self.filename)
                if not detailed:
                    self.results[analysis_str] = self.all_analyses[analysis_str].summarize_result(self.results[analysis_str])
        return self.join_analyses_results()

    def reset(self):
        self.notebook_IR = None
        self.active_analyses: list[str] = []

    def __str__(self) -> str:
        notebook = f""
        for i, cell in self.notebook_IR.items():
            notebook += f"[{i}:{cell}, last  run: {self.notebook_IR[i].last_ran_code}]"
        return f"Notebook: {notebook}\n Analyses: {self.active_analyses}"