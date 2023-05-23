# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
from .rows import Rows
from .columns import Columns

class DataFrame:
    def __init__(self, source: str, columns: Columns, rows: Rows):
        self.source: str = source
        self.columns: Columns = columns
        self.rows: Rows = rows

    def constraint(self, c_columns: Columns, c_rows: Rows):
        return DataFrame(self.source, self.columns & c_columns, self.rows & c_rows)

    def join(self, other: DataFrame) -> DataFrame:
        return DataFrame(self.source, self.columns | other.columns, self.rows | other.rows)

    def meet(self, other: DataFrame) -> DataFrame:
        return self.constraint(other.columns, other.rows)

    def __or__(self, other: DataFrame) -> DataFrame:
        return self.join(other)

    def __and__(self, other: DataFrame) -> DataFrame:
        return self.meet(other)

    def __sub__(self, other: DataFrame) -> set[DataFrame]:
        p_columns: Columns = self.columns - other.columns
        p_rows: list[Rows] = self.rows - other.rows
        product: set[DataFrame] = {DataFrame(self.source, p_columns, p_rows[0])}
        
        if len(p_rows) == 2:
            product.add(DataFrame(self.source, p_columns, p_rows[-1]))

        return product

    def overlap(self, other: DataFrame, weak: bool = False) -> bool:
        '''
        Weak overlap is a less strict version of overlap.
        It ignores the row intersection. Used for taint-based dataleak detection.
        '''
        if self.source != other.source:
            return False
        
        p_overlap: DataFrame = self & other
        return (weak or not p_overlap.rows.is_empty()) and p_overlap.columns.positive_columns() > 0

    def __eq__(self, other: DataFrame) -> bool:
        row_eq = self.rows == other.rows
        source_eq = self.source == other.source
        col_eq = self.columns.columns == other.columns.columns

        return row_eq and source_eq and col_eq

    def __ne__(self, other: DataFrame) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash((self.source, frozenset(self.columns.columns), self.rows.start, self.rows.end))

    def __str__(self):
        return (
            "\tDataFrame(\n\t\tsource: "
            + self.source
            + "\n\t\tcolumns: "
            + self.columns.__str__()
            + "\n\t\trows: "
            + self.rows.__str__()
            + "\n\t)"
        )

    def __repr__(self):
        return self.__str__()
