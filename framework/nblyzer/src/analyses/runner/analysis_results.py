# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
from copy import deepcopy
from enum import Enum

class ErrorType(Enum):
    CRITICAL = "CRITICAL"
    TERMINAL = "TERMINAL"

class ErrorInfo(dict):
    def __init__(self, cell_id, line, label, error_type, error_message):
        self.cell_id = cell_id
        self.line = line
        self.label = label
        self.error_type = error_type
        self.error_message = error_message

    def __repr__(self):
        return "line: " + str(self.line) + " in cell " + str(self.cell_id) + " label " + str(self.label) + " type " + self.error_type + " msg " + self.error_message

    def __eq__(self, other):
        if (isinstance(other, ErrorInfo)):
            return self.cell_id == other.cell_id and self.line == other.line and self.label == other.label and self.error_message == other.error_message and self.error_type == other.error_type
        return False

class PathResult:
    def __init__(self, path, error_infos):
        self.path = path
        self.error_infos:list[ErrorInfo] = error_infos

    def __repr__(self):
        return "Path: " + str(self.path) + "Errors: " + str(self.error_infos)

    def __eq__(self, __o: PathResult) -> bool:
        path_flag = self.path == __o.path 
        err_flag = True 
        for e in self.error_infos:
            err_flag = err_flag and (e in __o.error_infos)

        return err_flag

class Result:
    def __init__(self) -> None:
        self.path_results = list[PathResult]()

    def add_path_results(self, opath_results: list[PathResult]) -> None:
        self.path_results += opath_results

    def add_path_result(self, path_result: PathResult) -> None:
        self.path_results.append(path_result)
    
    def join_results(self, result: Result) -> None:
        self.add_path_results(result.path_results)

    def has_path_with_error_cell(self, cell_id: int):
        if not len(self.path_results):
            return None

        for path_result in self.path_results:
            if path_result.path[-1] == cell_id:
                return path_result
        return None

    def distinct_errors(self) -> Result:
        result: Result = Result()
        for path_result in self.path_results:
            if not result.has_path_with_error_cell(path_result.path[-1]):
                result.add_path_results([path_result])
        return result

    def dumps(self, with_path: bool = False) -> str:
        if not len(self.path_results):
            return ''
        resultJSON = "["
        for path_result in self.path_results:
            error_json = f'{{"cell_id":{path_result.path[-1]},"errors":['
            for err in path_result.error_infos:
                errty = err.error_type
                error_json += f'{{"line":{err.line},"label":"{err.label}", "error_type":"{errty}", "message":"{err.error_message}"}},'
            error_json = error_json[:-1] + ']'
            if with_path:
                error_json += f',"path":{path_result.path}'
            resultJSON += error_json + '},'
        resultJSON = resultJSON[:-1] + "]"
        return resultJSON
    
    def join_by_cell_id(self) -> Result:
        new_result = Result()
        for path_res in self.path_results:
            match_pr = new_result.has_path_with_error_cell(path_res.path[-1])
            if match_pr:
                match_pr.error_infos += deepcopy(path_res.error_infos)
            else:
                new_result.add_path_results([deepcopy(path_res)])
        return new_result

    def __eq__(self, __o: Result) -> bool:
        ret = False
        if len(self.path_results) != len(__o.path_results):
            return ret
        return self.path_results == __o.path_results 

