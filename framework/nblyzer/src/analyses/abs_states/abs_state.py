# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations
from abc import ABC, abstractmethod

class AbstractState(ABC):
    
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def __eq__(self, other: AbstractState) -> bool:
        '''
        Used for comparison of abstract states.
        Can be used e.g. for fixpoint detection.
        '''
        pass

    @abstractmethod
    def projection(self):
        '''
        Projection of a certain state will usually represent set or mapping 
        of certain variables and domain elements and be used when calculating 
        propagation condition.
        '''
        pass

    @abstractmethod
    def aug_join(self, other: AbstractState) -> AbstractState:
        '''
        Augmented join method. Nature of join itself is abstract state-specific.
        '''
        pass

    @abstractmethod
    def contains(self, other: AbstractState) -> bool:
        pass
    
    @abstractmethod
    def condition(self, cell_IR, node) -> list:
        '''
        Checks for errors in state of the cell, returns updated error list if found otherwise doesn't update error list 
        '''
        pass
