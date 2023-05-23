# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
from itertools import product
from math import ceil
from .data_frame import DataFrame
from .columns import Columns
from .rows import Rows

'''
Naming conventions:

l_ -> "list of"...
s_ -> "set of"...
o_ -> "of other" <=> (attr of a non self object)
'''

class DataFrameSet:
    def __init__(self, init_frames : dict[str, list[DataFrame]] = dict()) -> None:
        '''
        Mapping source names to matching Data Frame Lists because of possible Data Frames
        with same source but disjoint subdomains (e.g. disjoint row intervals), but still having solid
        performance thanks to dict lookup time.
        '''
        self.frames : dict[str, list[DataFrame]] = init_frames

    def constraint(self, c_columns: Columns, c_rows: Rows): 
        for l_df in self.frames.values(): 
            for i, df in enumerate(l_df):
                l_df[i] = df.constraint(c_columns, c_rows)

    def join(self, other: DataFrameSet) -> DataFrameSet:
        '''
        Iterate over the other dict and perform reduction as soon as overlapping is detected.
        '''
        product: DataFrameSet = DataFrameSet(dict(self.frames))

        for source, l_o_df in other.frames.items():
            for o_df in l_o_df:
                if source not in product.frames:
                    product.frames[source] = [o_df]
                    continue
                
                reduced: bool = False

                l_df = product.frames[source]
                for i, df in enumerate(l_df):
                    if df.overlap(o_df):
                        l_df[i] = df | o_df
                        reduced = True
                        break
                
                if reduced:
                    continue

                product.frames[source].append(o_df)

        return product

    def cartesian_overlap(self, other: DataFrameSet, weak: bool = False) -> bool:
        '''
        Multiple versions of overlap exist for the sake of data leak condition check.
        For example if two variables map to the same source and have disjunct, not empty usage sets
        and are both tainted, their row intersection does not matter.

        Strong overlap (or just overlap) means that the row intersection is taken into account.
        Weak overlap means that the row intersection is NOT taken into account.
        '''
        for o_source, l_o_df in other.frames.items():
            if o_source not in self.frames:
                continue

            for df, o_df in product(self.frames[o_source], l_o_df):
                if df.overlap(o_df, weak):
                    return True

        return False  

    def some_rows(self) -> bool:
        for l_df in self.frames.values():
            for df in l_df:
                if not df.rows.is_empty():
                    return True
        
        return False

    def meet(self, other: DataFrameSet) -> DataFrameSet:
        product: DataFrameSet = DataFrameSet(dict(self.frames))

        for source, l_o_df in other.frames.items():
            for o_df in l_o_df:
                if source not in product.frames:
                    continue
                
                l_o_df = product.frames[source]
                for i, df in enumerate(l_o_df):
                    if df.overlap(o_df):
                        l_o_df[i] &= o_df

        return product   

    def slice_rows(self, lw, up) -> None:
        '''
        This way of interval handling lets us handle 'recursive' slicing.
        I.e. df2 = df.iloc[2:15] -> df3 = df2.iloc[3:10] should result in 
        interval [5, 11] for df3 cause it is tracking the same source as df.
        
        If boundary is left unbounded copy the old one, else perform the slice.
        Note that the upper boundary is not inclusive, meaning that lw >= up implies
        empty rows interval.
        '''
        for l_df in self.frames.values():
            for df in l_df:
                n_start = df.rows.start if lw == None else (lw + df.rows.start if lw >= 0 else df.rows.end + lw + 1)
                n_end = df.rows.end if up == None else (up + df.rows.start - 1 if up >= 0 else df.rows.end + up)
        
                df.rows = Rows(n_start, n_end)

    def truncate_rows(self, percentage, inverse= False) -> None:
        for l_df in self.frames.values():
            for df in l_df: 
                if df.rows.is_empty():
                    return
                interval = df.rows.end - df.rows.start + 1
                chunk = interval - ceil(interval * percentage) if inverse else ceil(interval * percentage)
                df.rows = Rows(df.rows.start + (chunk if inverse else 0), df.rows.end - (0 if inverse else chunk))

    def rename_sources(self, new_source: str) -> None:
        victims: list[str] = [source for source in self.frames.keys()]

        for source in victims:
            for df in self.frames[source]:
                df.source = new_source
                
            self.frames[new_source] = self.frames[source]
            self.frames.pop(source)

    def drop_columns(self, column: str) -> None:
        for l_df in self.frames.values():
            for i, df in enumerate(l_df):
                l_df[i].columns = df.columns.join(Columns({column:False}))

    def drop_rows(self, row: int) -> None:
        for source, l_df in self.frames.items():
            l_repl = list[DataFrame]()

            for df in l_df:
                s_df = df - DataFrame(df.source, df.columns, Rows(row, row))
                l_repl.extend(s_df)

            self.frames[source] = l_repl

    def pick_columns(self, column_pres: dict[str, bool]) -> str:
        for l_df in self.frames.values():
            for df in l_df:
                df.columns = Columns(column_pres)

    def __or__(self, other: DataFrameSet) -> DataFrameSet:
        return self.join(other)

    def __and__(self, other: DataFrameSet) -> DataFrameSet:
        return self.meet(other)

    def __sub__(self, other: DataFrameSet) -> DataFrameSet:
        '''
        Unfinished. Not used for now anyway.
        '''
        for l_df in self.frames.values():
            for i, df in enumerate(l_df):
                for l_o_df in other.frames.values():
                    for o_df in l_o_df:
                        s_df = df - o_df 
                        self.frames.pop()
                        #TODO

    def __eq__(self, other: DataFrameSet) -> bool:
        return self.frames == other.frames

    def __str__(self) -> str:
        p = '\nDataFramesSet: [\n'
        for i, l_df in enumerate(self.frames.values()):
            for df in l_df:
                p += df.__str__() + ('\n' if i == len(self.frames) - 1 else ',\n')
        p += ']\n'
        return p

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, key: str) -> list[DataFrame]:
        return self.frames[key]

    def __eq__(self, other: DataFrameSet) -> bool:
        '''
        Used for testing only
        '''
        return self.frames == other.frames
