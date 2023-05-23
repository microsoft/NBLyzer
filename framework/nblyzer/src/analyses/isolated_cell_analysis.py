# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from .runner.analysis_results import PathResult, Result, ErrorInfo
from .runner.analysis_results import ErrorType
from .runner.analyses_utils import get_all_unbound_vars
from .analysis import Analysis

class IsolatedCellAnalysis(Analysis):
    def analyze_notebook(self, notebook_IR, old_cell_IR = None, level = 20, filename=""):
        unbound_vars = get_all_unbound_vars(notebook_IR)
        isolated_cells: Result = Result()
        for cell_id, data in notebook_IR.items():
            if not len(data.UDA.def_use_chains.unbound_names) and not len(unbound_vars.intersection(set(data.UDA.defined_vars.keys()))):
                path_result: PathResult = PathResult([cell_id], [])
                for label in data.UDA.defined_vars.keys():
                    for line, line_text in enumerate(data.cell_code.split('\n')):
                        if line_text.find(label) != -1:
                            path_result.error_infos.append(ErrorInfo(cell_id, line + 1, label, ErrorType.TERMINAL, "This cell contains only unused variables."))
                            break
                if not len(path_result.error_infos):
                    path_result.error_infos.append(ErrorInfo(cell_id, 1, "", ErrorType.TERMINAL, "This cell contains only unused variables."))
                isolated_cells.add_path_results([path_result])
        return isolated_cells
