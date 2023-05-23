# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
from sre_parse import fix_flags
from nblyzer import NBlyzer
from argparse import ArgumentParser
from events import RunBatchEvent
from analyses.runner.analysis_results import ErrorInfo, PathResult, Result, ErrorType
from resource_utils.rsrc_mngr import ResourceManager
from resource_utils.utils import is_script
import csv
import os
from tqdm import tqdm
import json
import constants

def make_error_infos(cell_id, errs):
    error_infos = []
    for e in errs:
        err_ty = ErrorType.TERMINAL if e['error_type'] == "ErrorType.TERMINAL" else  ErrorType.CRITICAL
        error_infos.append(ErrorInfo(cell_id, e['line'], e['label'], err_ty, e['message']))
    return error_infos

def make_path_result(cell_id, pr, errs):
    path_res = PathResult(pr, make_error_infos(cell_id, errs))
    return path_res

def make_result(res) -> Result:
    result = Result()
    for r in res:
        path = make_path_result(r['cell_id'], r['path'], r['errors'])
        result.add_path_result(path)
    return result

def tester(folder):
    folder = "./nblyzer_backend/tests/resources/rtests/" if folder is None else folder
    mng = ResourceManager()
    print("using folder "  + folder)
    dir_list = os.listdir(folder)
    for f in tqdm(dir_list):
        if not f.endswith("pynb") and not f.endswith("ipynb"):
            continue

        print("Test file: " + f)
        notebook = mng.grab_local_json(folder+f)
        nblyzer = NBlyzer(level=5)
        nblyzer.load_notebook(notebook["cells"])
        nblyzer.add_analyses([constants.DATA_LEAK, constants.STALE, constants.ISOLATED, constants.IDLE])
        event = RunBatchEvent(0)
        results = nblyzer.execute_event(event)
        with open(folder + f + ".out", 'r') as file:
            r1 = make_result(json.load(file))

        if r1 != results:
            print("Error: test file " + f + " does not match!")
            print("Expected: ")
            print(r1.dumps(True))
            print("Found: ")
            print(results.dumps(True))
        else:
            print("PASSED")

        print("\n")

def main():
    parser = ArgumentParser(description="NBLyzer tester version 1.0 ")
    parser.add_argument("-f", "--folder",  type=str, help='Tests folder')
    args = parser.parse_args()
    tester(args.folder)

if __name__ == "__main__":
    main()
