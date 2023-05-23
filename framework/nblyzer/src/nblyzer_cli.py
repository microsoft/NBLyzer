# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from argparse import ArgumentParser

from .nblyzer import NBLyzer
from .events import RunBatchEvent
from .resource_utils.rsrc_mngr import ResourceManager
from .resource_utils.utils import is_script

def nblyzer(filename, notebook,  analyses,  start, level=5):
    code_nblyzer = NBLyzer(level = level)
    assert(not (filename and notebook))
    mng = ResourceManager()
    if (notebook is None):
        assert(filename)
        if is_script(filename):
            notebook = mng.grab_local_file(filename)
            code_nblyzer.load_script(notebook)
        else:
            notebook = mng.grab_local_json(filename)
            code_nblyzer.load_notebook(notebook["cells"])
    else:
        code_nblyzer.load_notebook(notebook["cells"])
    
    code_nblyzer.add_analyses(analyses)
    event = RunBatchEvent(start)
    results = code_nblyzer.execute_event(event).dumps(True)

    return results

def main():
    parser = ArgumentParser(description="NBLyzer version 1.0 ")
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-f", "--filename",  type=str, help='Filename of notebook.')
    group.add_argument("-n", "--notebook", type=str, help='Notebook json string.')
    parser.add_argument("-a", "--analyses", nargs="+", type=str, default=[], help='Analyses to perform.')
    parser.add_argument("-s", "--start", type=int, default=0, help='Starting cell ID (default is 0).')
    parser.add_argument("-l", "--level", nargs="?", type=int, default=5, help='Depth level of the analysis (default is inf).')
    args = parser.parse_args()

    results = nblyzer(args.filename, args.notebook, args.analyses, args.start, args.level)
    print(results)

if __name__ == "__main__":
    main()
