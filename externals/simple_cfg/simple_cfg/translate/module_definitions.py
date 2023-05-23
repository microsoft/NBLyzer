import ast

project_definitions = dict()

class ModuleDefinition():
    module_definitions = None
    name = None
    node = None
    path = None

    def __init__(
        self,
        local_module_definitions,
        name,
        parent_module_name,
        path
    ):
        self.module_definitions = local_module_definitions
        self.parent_module_name = parent_module_name
        self.path = path

        if parent_module_name:
            if isinstance(parent_module_name, ast.alias):
                self.name = parent_module_name.name + '.' + name
            else:
                self.name = parent_module_name + '.' + name
        else:
            self.name = name

    def __str__(self):
        name = 'NoName'
        node = 'NoNode'
        if self.name:
            name = self.name
        if self.node:
            node = str(self.node)
        return "Path:" + self.path + " " + self.__class__.__name__ + ': ' + ';'.join((name, node))


class LocalModuleDefinition(ModuleDefinition):
    pass


class ModuleDefinitions():
    def __init__(
        self,
        import_names=None,
        module_name=None,
        is_init=False,
        filename=None
    ):
        self.import_names = import_names
        self.module_name = module_name
        self.is_init = is_init
        self.filename = filename
        self.definitions = list()
        self.classes = list()
        self.import_alias_mapping = dict()

    def append_if_local_or_in_imports(self, definition):
        if isinstance(definition, LocalModuleDefinition):
            self.definitions.append(definition)
        elif self.import_names == ["*"]:
            self.definitions.append(definition)
        elif self.import_names and definition.name in self.import_names:
            self.definitions.append(definition)
        elif (self.import_alias_mapping and definition.name in
              self.import_alias_mapping.values()):
            self.definitions.append(definition)

        if definition.parent_module_name:
            self.definitions.append(definition)

        if definition.node not in project_definitions:
            project_definitions[definition.node] = definition

    def get_definition(self, name):
        for definition in self.definitions:
            if definition.name == name:
                return definition

    def set_definition_node(self, node, name):
        definition = self.get_definition(name)
        if definition:
            definition.node = node

    def __str__(self):
        module = 'NoModuleName'
        if self.module_name:
            module = self.module_name

        if self.definitions:
            if isinstance(module, ast.alias):
                return (
                    'Definitions: "' + '", "'
                    .join([str(definition) for definition in self.definitions]) +
                    '" and module_name: ' + module.name +
                    ' and filename: ' + str(self.filename) +
                    ' and is_init: ' + str(self.is_init) + '\n')
            return (
                'Definitions: "' + '", "'
                .join([str(definition) for definition in self.definitions]) +
                '" and module_name: ' + module +
                ' and filename: ' + str(self.filename) +
                ' and is_init: ' + str(self.is_init) + '\n')
        else:
            if isinstance(module, ast.alias):
                return (
                    'import_names is ' + str(self.import_names) +
                    ' No Definitions, module_name: ' + str(module.name) +
                    ' and filename: ' + str(self.filename) +
                    ' and is_init: ' + str(self.is_init) + '\n')
            return (
                'import_names is ' + str(self.import_names) +
                ' No Definitions, module_name: ' + str(module) +
                ' and filename: ' + str(self.filename) +
                ' and is_init: ' + str(self.is_init) + '\n')
