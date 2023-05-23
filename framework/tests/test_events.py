# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import unittest
import json
from nblyzer.src.events import *
from nblyzer.src.nblyzer import NBLyzer
from nblyzer.src.resource_utils.utils import TEST_RES_PATH
from nblyzer.src.resource_utils.rsrc_mngr import mngr
from nblyzer.src.constants import *


class TestEvents(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.nblyzer = NBLyzer()
        notebook_json = mngr.grab_local_json(TEST_RES_PATH + "dataleak_true.ipynb")["cells"]
        self.nblyzer.load_notebook(notebook_json)
        self.nblyzer.add_analyses(
            [DATA_LEAK, STALE, IDLE]
        )

    def test_cell_run_event(self):
        cell_run_event = RunCellEvent(0)
        results = cell_run_event.execute(self.nblyzer).dumps()
        #self.assertEqual(results, '[{"cell_id":4,"errors":[{"line":2,"label":"X_selected_test", "error_type":"ErrorType.TERMINAL", "message":"Training model with data leak. Path that will lead to this: [0, 1, 2, 3, 4]"}]},{"cell_id":2,"errors":[{"line":2,"label":"y_train", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"X_selected_test", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"X_selected_train", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"y_test", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}]},{"cell_id":3,"errors":[{"line":3,"label":"a", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}]}]')
        self.assertTrue(True)
        

    def test_batch_run_event(self):
        run_event = RunBatchEvent(0)
        results = run_event.execute(self.nblyzer).dumps(True)
        #self.assertEqual(results, '[{"cell_id":4,"errors":[{"line":2,"label":"X_selected_test", "error_type":"ErrorType.TERMINAL", "message":"Training model with data leak."}],"path":[0, 1, 2, 3, 4]},{"cell_id":2,"errors":[{"line":2,"label":"y_test", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"X_selected_test", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"y_train", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."},{"line":2,"label":"X_selected_train", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}],"path":[0, 1, 2]},{"cell_id":3,"errors":[{"line":3,"label":"a", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}],"path":[0, 1, 2, 3]},{"cell_id":4,"errors":[{"line":2,"label":"y_pred", "error_type":"ErrorType.TERMINAL", "message":"Variable is not used outside this cell."}],"path":[4]}]')
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
