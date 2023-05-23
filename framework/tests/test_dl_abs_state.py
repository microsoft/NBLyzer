# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from ast import Assert
import unittest

from nblyzer.src.IR.intermediate_representations import IntermediateRepresentations
from nblyzer.src.analyses.abs_states.dataleak_abs_state import DataLeakAbstractDomain, DataLeakAbstractState, Usage
from nblyzer.src.analyses.abs_domains.dataleak_lattice.data_frame_sets import DataFrameSet
from nblyzer.src.analyses.abs_domains.dataleak_lattice.data_frame import DataFrame
from nblyzer.src.analyses.abs_domains.dataleak_lattice.columns import Columns
from nblyzer.src.analyses.abs_domains.dataleak_lattice.rows import Rows
from simple_cfg.cfg_nodes import Node
from nblyzer.src.analyses.runner.analysis_results import ErrorInfo, ErrorType

class TestDataFrames(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        return super().setUp()

    def test_df_join(self):
        d1: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona12': False, 'kolona13': True}),
            Rows(8, 15),
        )

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona21': True, 'kolona22': False, 'kolona13': True}),
            Rows(10, 22),
        )

        self.assertEqual(
            d1 | d2,
            DataFrame(
                'df',
                Columns(
                    {
                        'kolona11': True,
                        'kolona12': False,
                        'kolona13': True,
                        'kolona21': True,
                        'kolona22': False,
                    }
                ),
                Rows(8, 22),
            ),
        )

        # Test reduction operator
        d1.columns.columns['kolona13'] = False
        self.assertEqual(
            d1 | d2,
            DataFrame(
                'df',
                Columns(
                    {
                        'kolona11': True,
                        'kolona12': False,
                        'kolona21': True,
                        'kolona22': False,
                    }
                ),
                Rows(8, 22),
            ),
        )

    def test_df_meet(self):
        d1: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': False, 'kolona13': True}),
            Rows(10, 15),
        )

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': True, 'kolona23': True}),
            Rows(13, 22),
        )
        self.assertEqual(
            d1 & d2,
            DataFrame('df', Columns({'kolona11': True}), Rows(13, 15)),
        )

    def test_df_overlap(self):
        d1: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': False, 'kolona13': True}),
            Rows(10, 15),
        )

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': True, 'kolona23': True}),
            Rows(13, 22),
        )

        self.assertEqual(True, d1.overlap(d2))

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': False, 'kolona22': True, 'kolona23': False}),
            Rows(13, 22),
        )

        self.assertEqual(False, d1.overlap(d2))

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': True, 'kolona23': True}),
            Rows(4, 8),
        )

        self.assertEqual(False, d1.overlap(d2))

    def test_df_subtraction(self):
        d1: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': False, 'kolona13': True}),
            Rows(10, 15),
        )

        d2: DataFrame = DataFrame(
            'df',
            Columns({'kolona11': True, 'kolona22': True, 'kolona23': True}),
            Rows(13, 22),
        )

        d_ref: DataFrame = DataFrame(
            'df', Columns({'kolona13': True, 'kolona22': False}), Rows(10, 12)
        )
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(15, 20)
        d_ref.rows = Rows(10, 14)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(6, 12)
        d_ref.rows = Rows(13, 15)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(10, 10)
        d_ref.rows = Rows(11, 15)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(15, 15)
        d_ref.rows = Rows(10, 14)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(10, 15)
        d_ref.rows = Rows(-1, -1)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(10, 11)
        d_ref.rows = Rows(12, 15)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(14, 15)
        d_ref.rows = Rows(10, 13)
        self.assertEqual(d1 - d2, {d_ref})

        d2.rows = Rows(12, 13)
        d_ref.rows = Rows(10, 11)
        d_ref2: DataFrame = DataFrame(
            'df', Columns({'kolona13': True, 'kolona22': False}), Rows(14, 15)
        )
        self.assertEqual(d1 - d2, {d_ref, d_ref2})

        d2.columns = Columns(
            {'kolona11': True, 'kolona22': False, 'kolona13': True, 'kolona33': False}
        )
        d_ref.columns = d_ref2.columns = Columns({})

        self.assertEqual(d1 - d2, {d_ref, d_ref2})

    def test_data_frame_sets(self):
        dfs1: DataFrameSet = DataFrameSet(
            {
                'file1': [DataFrame('file1', Columns({'id': True}), Rows(1, 10))],
                'file2': [DataFrame('file2', Columns({'name': True}), Rows(0, 100))],
            }
        )
        dfs2 = DataFrameSet(
            {
            'file1': [DataFrame('file1', Columns({'id': True}), Rows(9, 12))],
            'file3': [DataFrame('file3', Columns({'zip': True}), Rows(0, 100))],
            }
        )

        ref_dfs = DataFrameSet(
            {
            'file1': [DataFrame('file1', Columns({'id': True}), Rows(1, 12))],
            'file2': [DataFrame('file2', Columns({'name': True}), Rows(0, 100))],
            'file3': [DataFrame('file3', Columns({'zip': True}), Rows(0, 100))],
            }
        )

    
        self.assertEqual(dfs1 | dfs2, ref_dfs)

        dfs1.frames['file1'][0].rows = Rows(1, 6)


        ref_dfs = DataFrameSet(
            {
            'file1': [DataFrame('file1', Columns({'id': True}), Rows(1, 6)),
                    DataFrame('file1', Columns({'id': True}), Rows(9, 12))],
            'file2': [DataFrame('file2', Columns({'name': True}), Rows(0, 100))],
            'file3': [DataFrame('file3', Columns({'zip': True}), Rows(0, 100))],
            }
        )

        self.assertEqual(dfs1 | dfs2, ref_dfs)

    def test_condition_detection(self):

        dfs1: DataFrameSet = DataFrameSet({
            'x_selected': [DataFrame('x_selected', Columns({'col1': True, 'col2': True}), Rows(0, 2))]
        })

        dfs2: DataFrameSet = DataFrameSet({
            'x_selected': [DataFrame('x_selected', Columns({'col1': True, 'col2': True}), Rows(4, 5))]
        })        

        a_state: DataLeakAbstractState = DataLeakAbstractState()

        a_state.state['X_train'] = DataLeakAbstractDomain(dfs1, True, {Usage.TRAIN})
        a_state.state['X_test'] = DataLeakAbstractDomain(dfs2, True, {Usage.TEST})
        errors = []
        a_state.condition(IntermediateRepresentations("", 1), Node("", None, line_number=1, path=1), errors)
        self.assertEqual(errors, [ErrorInfo(1, 1, "", ErrorType.TERMINAL, "Training model with data leak.")])

        a_state.state['X_test'] = DataLeakAbstractDomain(dfs2, False, {Usage.TEST})
        errors = []
        a_state.condition(IntermediateRepresentations("", 1), Node("", None, line_number=1, path=1), errors)
        self.assertEqual(errors, [])

        dfs2.frames['x_selected'][0].rows = Rows(2, 4)

        a_state.state['X_train'] = DataLeakAbstractDomain(dfs1, False, {Usage.TRAIN})
        a_state.state['X_test'] = DataLeakAbstractDomain(dfs2, True, {Usage.TEST})

        errors = []
        a_state.condition(IntermediateRepresentations("", 1), Node("", None, line_number=1, path=1), errors)
        self.assertEqual(errors, [ErrorInfo(1, 1, "", ErrorType.TERMINAL, "Training model with data leak.")])

        dfs1.frames['x_selected'][0].source = 'x_selected2'
        errors = []
        a_state.condition(IntermediateRepresentations("", 1), Node("", None, line_number=1, path=1), errors)
        self.assertEqual(errors, [])

if __name__ == "__main__":
    unittest.main()
