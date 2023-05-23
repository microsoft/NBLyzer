# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
import sys


class Columns:
    """
    Column domain with defined join and meet operators and appropriate reduction operators.
    """

    def __init__(self, init_columns: dict[str, bool] = dict(), all = False):
        '''
        Here we're "abusing" the dictionary instead of set which helps because of the need
        of internal reduction operator.

        Mapping column_name -> column_presence. column_presence will have value True if the named
        column is present within the set while False value claims that the named column is not present.
        As in theoretical model, complete absence of mapping for some column means that column's
        presence status is unknown (could be either of two)
        '''
        self.columns: dict[str, bool] = init_columns
        self.all = all

    def size(self) -> int:
        if self.all:
            return sys.maxsize
        return len(self.columns)

    def join(self, other: Columns) -> Columns:
        '''
        Joins two column sets in a new one and performs reduction operator simultaneously.
        This way the domain is always in canonical form.
        '''        
        product : Columns = Columns(self.columns.copy())

        for o_column, o_presence in other.columns.items():
            if o_column not in product.columns:
                product.columns[o_column] = o_presence
                continue

            if product.columns[o_column] != o_presence:
                product.columns.pop(o_column)

        product.all = self.all or other.all

        return product

    def meet(self, other: Columns) -> Columns:
        '''
        Meets (performs intersection) on two column sets in a new set.
        Two columns are equal iff they have the same name and same presence status.
        '''
        return Columns(dict(self.columns.items() & other.columns.items()), all=self.all and other.all)

    def positive_columns(self) -> int:
        if self.all:
            return sys.maxsize
        return len([col for col, pres in self.columns.items() if pres])

    def __or__(self, other: Columns) -> Columns:
        return self.join(other)

    def __and__(self, other: Columns) -> Columns:
        return self.meet(other)

    def __sub__(self, other: Columns) -> Columns:

        product : Columns = Columns(self.columns.copy())

        for o_column, o_presence in other.columns.items():
            if o_column in product.columns and product.columns[o_column] == o_presence:
                product.columns.pop(o_column)

        return product

    def __str__(self):
        return self.columns.__str__() if bool(self.columns) else '{~initial~}'
