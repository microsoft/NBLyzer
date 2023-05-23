# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import unittest
from nblyzer.src.analyses.stale_cell_analysis import StaleCellAnalysis
from nblyzer.src.IR.intermediate_representations import IntermediateRepresentations
from nblyzer.src.resource_utils.utils import load_notebook, TEST_RES_PATH
from nblyzer.src.resource_utils.rsrc_mngr import mngr


class TestStaleCellAnalysis(unittest.TestCase):
    def test_analyze_notebook(self):
        test_IR = load_notebook(
            mngr.grab_local_json(TEST_RES_PATH + "Test.ipynb")["cells"]
        )
        analyzer_test: StaleCellAnalysis = StaleCellAnalysis()
        analyzer_test.find_necessary_cells(test_IR)
        result = analyzer_test.analyze_notebook(
            test_IR, IntermediateRepresentations("x = 20", 0)
        )
        result = analyzer_test.summarize_result(result)
        analyzer_test.find_necessary_cells(test_IR)
        self.assertEqual(
            analyzer_test.summarize_result(
                analyzer_test.analyze_notebook(
                    test_IR, IntermediateRepresentations("x = 20", 0)
                )
            ).dumps(),
            '[{"cell_id":4,"errors":[{"line":1,"label":"z", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}]},{"cell_id":5,"errors":[{"line":1,"label":"z", "error_type":"ErrorType.CRITICAL", "message":"Variable uses outdated values."}]}]',
        )

        basic_IR = load_notebook(
            mngr.grab_local_json(TEST_RES_PATH + "Basic.ipynb")["cells"]
        )
        analyzer_basic = StaleCellAnalysis()
        analyzer_basic.find_necessary_cells(basic_IR)
        self.assertEqual(
            analyzer_basic.summarize_result(
                analyzer_basic.analyze_notebook(
                    basic_IR, IntermediateRepresentations("y = 20", 1)
                )
            ).dumps(), 
            ''
        )


if __name__ == "__main__":
    unittest.main()
