# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import unittest
from nblyzer.src.nblyzer_cli import *
from nblyzer.src.resource_utils.utils import TEST_RES_PATH
from nblyzer.src.resource_utils.rsrc_mngr import mngr
from nblyzer.src.constants import *

class TestNBLyzerCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.test_notebooks = ["Test.ipynb", "Test.ipynb", "Basic.ipynb"]
        self.analyses = [
            STALE,
            SAFE_PATH,
            FRESH,
            IDLE,
            ISOLATED,
        ]
        self.expected_results_test_AST = {
            STALE: [],
            SAFE_PATH: [[3, 1, 2, 4, 5], [3, 2, 1, 4, 5], []],
            FRESH: [[4, 5, 6]],
            IDLE: [[5, 6]],
            ISOLATED: [[6]],
        }
        self.expected_results_basic_AST = {
            STALE: [],
            SAFE_PATH: [],
            FRESH: [0, 1],
            IDLE: [0, 1],
            ISOLATED: [0, 1],
        }
        return super().setUp()

    """
    def test_AST_analyses(self):
        results_test = json.loads(
            nblyzer(
                filename=None,
                notebook=mngr.grab_local(TEST_RES_PATH + "Test.ipynb"),
                analyses=self.analyses,
                start=0,
                level = 10
            )
        )
        for analysis in self.analyses:
            self.assertIn(
                results_test[analysis], self.expected_results_test_AST[analysis]
            )

        results_basic = json.loads(
            nblyzer(
                filename=TEST_RES_PATH + "Basic.ipynb",
                notebook=None,
                analyses=self.analyses,
                start=1,
                level=10
            )
        )
        for analysis in self.analyses:
            self.assertEqual(
                results_basic[analysis], self.expected_results_basic_AST[analysis]
            )
    """
    def test_dataleak(self):
        results_true = nblyzer(
                filename=None,
                notebook=mngr.grab_local_json(TEST_RES_PATH + "dataleak_true.ipynb"),
                analyses=[DATA_LEAK],
                start=0,
                level=10
            )
        self.assertEqual(results_true, '[{"cell_id":4,"errors":[{"line":2,"label":"X_selected_test", "error_type":"ErrorType.TERMINAL", "message":"Training model with data leak."}],"path":[0, 1, 2, 3, 4]}]')
        results_false = nblyzer(
                filename=None,
                notebook=mngr.grab_local_json(TEST_RES_PATH + "dataleak_false.ipynb"),
                analyses=[DATA_LEAK],
                start=0,
                level=10
            )
        self.assertEqual(results_false, '')

if __name__ == "__main__":
    unittest.main()