# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
import sys

class Rows:
    def __init__(self, start = 0, end = sys.maxsize):
        if start > end:
            self.start = self.end = -1
            return

        self.start = start
        self.end = end

    def size(self) -> int:
        return self.end - self.start + 1

    def is_empty(self) -> bool:
        return self.start == -1 and self.end == -1

    def lw(self):
        return self.start
    def up(self):
        return self.end

    def join(self, other: Rows) -> Rows:
        p_start = min(self.start, other.start)
        p_end = max(self.end, other.end)

        return Rows(p_start, p_end)

    def meet(self, other: Rows) -> Rows:
        p_start = max(self.start, other.start)
        p_end = min(self.end, other.end)

        return Rows(p_start, p_end)

    def __or__(self, other: Rows) -> Rows:
        return self.join(other)

    def __and__(self, other: Rows) -> Rows:
        return self.meet(other)

    def __sub__(self, other: Rows) -> list[Rows]:
        if self.start <= other.start <= self.end <= other.end:
            return [Rows(self.start, other.start - 1)]
        
        if other.start <= self.start <= other.end <= self.end:
            return [Rows(other.end + 1, self.end)]

        if other.start <= self.start <= self.end <= other.end:
            return [Rows(-1, -1)]
        
        if self.start < other.start <= other.end < self.end:
            return [Rows(self.start, other.start - 1), Rows(other.end + 1, self.end)]

        return [Rows(self.start, self.end)]

    def __eq__(self, other: Rows) -> bool:
        if self.is_empty():
            return other.is_empty()

        return self.start == other.start and self.end == other.end

    def __str__(self):
        return '[' + str(self.start) + ', ' + str(self.end) + ']'
