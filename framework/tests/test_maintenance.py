# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import unittest
import json
from nblyzer.src.analyses.dataleak_analysis import DataLeakAnalysis
from nblyzer.src.analyses.stale_cell_analysis import StaleCellAnalysis
from nblyzer.src.resource_utils.utils import load_notebook, TEST_RES_PATH
from nblyzer.src.resource_utils.rsrc_mngr import mngr
from nblyzer.src.nblyzer import NBLyzer
from nblyzer.src.constants import *


class Testnblyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.notebook_json = mngr.grab_local_json(TEST_RES_PATH + "dataleak_true.ipynb")[
            "cells"
        ]
        self.nblyzer = NBLyzer()
        self.reference_notebook_IR = load_notebook(self.notebook_json)

    def test_load_notebook(self):
        reference_notebook = load_notebook(self.notebook_json)
        self.nblyzer.load_notebook(self.notebook_json)
        for i in reference_notebook.keys():
            self.assertEqual(reference_notebook[i], self.nblyzer.notebook_IR[i])

    def test_add_analyses(self):
        self.nblyzer.add_analyses([DATA_LEAK])
        self.assertIn(DATA_LEAK, self.nblyzer.active_analyses)
        self.assertIsInstance(
            self.nblyzer.all_analyses[DATA_LEAK], DataLeakAnalysis
        )

        self.nblyzer.add_analyses([STALE, FRESH])
        self.assertIn(STALE, self.nblyzer.active_analyses)
        self.assertIsInstance(
            self.nblyzer.all_analyses[STALE], StaleCellAnalysis
        )

    def test_update_abstract_states(self):
        """
        TODO: Update pickles to match new abstract state model
        """
        # self.nblyzer.add_analyses([constants.DATA_LEAK])

        # cell_0 = self.reference_notebook_IR[0]
        # self.nblyzer.update_abstract_states(cell_0)
        # as_0 = pickle.loads(mngr.grab_remote("abstract_state_0.pickle"))
        # self.assertEqual(as_0, self.nblyzer.active_analyses[constants.DATA_LEAK].abstract_state)

        # cell_1 = self.reference_notebook_IR[1]
        # self.nblyzer.update_abstract_states(cell_1)
        # as_1 = pickle.loads(mngr.grab_remote("abstract_state_1.pickle"))
        # self.assertEqual(as_1, self.nblyzer.active_analyses[constants.DATA_LEAK].abstract_state)

        # cell_2 = self.reference_notebook_IR[2]
        # self.nblyzer.update_abstract_states(cell_2)
        # as_2 = pickle.loads(mngr.grab_remote("abstract_state_2.pickle"))
        # self.assertEqual(as_2, self.nblyzer.active_analyses[constants.DATA_LEAK].abstract_state)

        # cell_3 = self.reference_notebook_IR[3]
        # self.nblyzer.update_abstract_states(cell_3)
        # as_3 = pickle.loads(mngr.grab_remote("abstract_state_3.pickle"))
        # self.assertEqual(as_3, self.nblyzer.active_analyses[constants.DATA_LEAK].abstract_state)

        # cell_4 = self.reference_notebook_IR[4]
        # self.nblyzer.update_abstract_states(cell_4)
        # as_4 = pickle.loads(mngr.grab_remote("abstract_state_4.pickle"))
        # self.assertEqual(as_4, self.nblyzer.active_analyses[constants.DATA_LEAK].abstract_state)

if __name__ == "__main__":
    unittest.main()
    