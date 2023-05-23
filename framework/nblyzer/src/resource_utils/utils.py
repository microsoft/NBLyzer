# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from ..IR.intermediate_representations import IntermediateRepresentations

TEST_RES_PATH = "./tests/resources/"

def is_script(filename):
    return filename.endswith(".py")

def load_notebook(notebook_json):
    notebook_IR = {}

    if notebook_json:
        for cnt, cell in enumerate(notebook_json):
            if (cell["cell_type"] != "code") or (not cell["source"]):
                continue
            if isinstance(cell["source"], list):
                cell["source"] = "".join(cell["source"])

            notebook_IR[cnt] = IntermediateRepresentations(cell["source"], cnt)

    return notebook_IR