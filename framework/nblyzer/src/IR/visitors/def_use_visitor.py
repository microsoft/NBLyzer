# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import beniget
from beniget.beniget import DeclarationStep

class DefUseVisitor(beniget.DefUseChains):  
    def __init__(self, filename=None):
        self.unbound_names = set()
        super().__init__(filename=filename)
        
    def unbound_identifier(self, name, node):
        self.unbound_names.add(name)