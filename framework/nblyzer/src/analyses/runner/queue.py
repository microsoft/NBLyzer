# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from queue import Queue

class FifoQueue():
    def __init__(self) -> None:
        self.q: Queue = Queue()

    def pop(self):
        return self.q.get_nowait()

    def push(self, e):
        self.q.put_nowait(e)

    def populate(self, l: list) -> None:
        for e in l:
            self.push(e)

    def empty(self) -> bool:
        return self.q.empty()


