import ast

class RHSVisitor(ast.NodeVisitor):
    def __init__(self):
        self.result = list()

    def visit_Constant(self, node):
        self.result.append(node.value)

    def visit_Name(self, node):
        self.result.append(node.id)

    def visit_Call(self, node):
        # for calls with RHS variable names
        if hasattr(node.func, 'value'):
            node.func.value.id_attr = list()
        if node.args:
            for arg in node.args:
                self.visit(arg)
                if hasattr(node.func, 'attr'):
                    # pd.merge (TODO: possibly some other functions that operate similarly)
                    if node.func.attr == 'merge':
                        if (isinstance(arg, ast.Subscript)):
                            node.func.value.id_attr.append(arg.value) # used in calls: df1.merge(df2) -> 'df2'
                        elif isinstance(arg, ast.Call):
                            node.func.value.id_attr.append(arg.func) # used in calls: df1.merge(df2) -> 'df2'
                        else:
                            node.func.value.id_attr.append(arg.id) # used in calls: df1.merge(df2) -> 'df2'
                    elif node.func.attr == 'genfromtxt' and hasattr(arg, 's'):
                        node.func.value.id_attr.append(arg.s) # used in calls: np.genfromtxt('data.csv') ->  'data.csv'
        if node.keywords:
            for keyword in node.keywords:
                self.visit(keyword)

    def visit_IfExp(self, node):
        # The test doesn't taint the assignment
        self.visit(node.body)
        self.visit(node.orelse)

    @classmethod
    def result_for_node(cls, node):
        visitor = cls()
        visitor.visit(node)
        return visitor.result
