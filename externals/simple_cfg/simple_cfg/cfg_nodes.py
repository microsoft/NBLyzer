from collections import namedtuple

from .visitors import LabelVisitor

ControlFlowNode = namedtuple(
    'ControlFlowNode',
    (
        'test',
        'last_nodes',
        'break_statements'
    )
)

class IgnoredNode():
    pass


class ConnectToExitNode():
    pass

class Node():
    id = 0
    def __init__(self, label, ast_node, *, line_number=None, path):
        Node.id += 1        
        self.label = label
        self.ast_node = ast_node
        if line_number:
            self.line_number = line_number
        elif ast_node:
            self.line_number = ast_node.lineno
        else:
            self.line_number = None
        self.path = path
        self.ingoing = list()
        self.outgoing = list()

    def as_dict(self):
        return {
            'label': self.label.encode('utf-8').decode('utf-8'),
            'line_number': self.line_number,
            'path': self.path,
        }

    def connect(self, successor):
        if isinstance(self, ConnectToExitNode) and not isinstance(successor, EntryOrExitNode):
            return

        self.outgoing.append(successor)
        successor.ingoing.append(self)

    def connect_predecessors(self, predecessors):
        for n in predecessors:
            self.ingoing.append(n)
            n.outgoing.append(self)

    def __str__(self):
        return ''.join((' Label: ', self.label))

    def __repr__(self):
        label = ' '.join(('Label: ', self.label))
        line_number = 'Line number: ' + str(self.line_number)
        outgoing = ''
        ingoing = ''
        if self.ingoing:
            ingoing = ' '.join(('ingoing:\t', str([x.label for x in self.ingoing])))
        else:
            ingoing = ' '.join(('ingoing:\t', '[]'))

        if self.outgoing:
            outgoing = ' '.join(('outgoing:\t', str([x.label for x in self.outgoing])))
        else:
            outgoing = ' '.join(('outgoing:\t', '[]'))

        return '\n' + '\n'.join((label, line_number, ingoing, outgoing))

class BreakNode(Node):
    def __init__(self, ast_node, *, path):
        super().__init__(
            self.__class__.__name__,
            ast_node,
            path=path
        )

class CondNode(Node):
    def __init__(self, test_node, ast_node, *, path):
        label_visitor = LabelVisitor()
        label_visitor.visit(test_node)
        self.test = test_node
        self.positive_nodes = []

        super().__init__(
            'cond ' + label_visitor.result + ':',
            ast_node,
            path=path
        )

class TryNode(Node):
    def __init__(self, ast_node, *, path):
        super().__init__(
            'try:',
            ast_node,
            path=path
        )

class EntryOrExitNode(Node):
    def __init__(self, label):
        super().__init__(label, None, line_number=None, path=None)

class RaiseNode(Node, ConnectToExitNode):
    def __init__(self, ast_node, *, path):
        label_visitor = LabelVisitor()
        label_visitor.visit(ast_node)

        super().__init__(
            label_visitor.result,
            ast_node,
            path=path
        )

class AssignmentNode(Node):
    def __init__(self, label, left_hand_side, ast_node, right_hand_side, *, 
    right_hand_side_literals=[], line_number=None, path):
        super().__init__(label, ast_node, line_number=line_number, path=path)
        self.left_hand_side = left_hand_side
        self.right_hand_side = right_hand_side

    def __repr__(self):
        output_string = super().__repr__()
        output_string += '\n'
        return ''.join(output_string)

class RestoreNode(AssignmentNode):
    def __init__(self, label, left_hand_side, right_hand_side_variables, *, line_number, path):
        super().__init__(label, left_hand_side, None, right_hand_side_variables, line_number=line_number, path=path)


class BBorBInode(AssignmentNode):
    def __init__(self, label, left_hand_side, ast_node, right_hand_side_variables, *, line_number, path, func_name):
        super().__init__(label, left_hand_side, ast_node, right_hand_side_variables, line_number=line_number, path=path)
        self.args = list()
        self.inner_most_call = self
        self.func_name = func_name


class AssignmentCallNode(AssignmentNode):
    def __init__(
        self,
        label,
        left_hand_side,
        ast_node,
        right_hand_side_variables,
        *,
        line_number,
        path,
        call_node
    ):
        super().__init__(
            label,
            left_hand_side,
            ast_node,
            right_hand_side_variables,
            line_number=line_number,
            path=path
        )
        self.call_node = call_node
        self.blackbox = False


class ReturnNode(AssignmentNode, ConnectToExitNode):
    def __init__(
        self,
        label,
        left_hand_side,
        ast_node,
        right_hand_side_variables,
        *,
        path
    ):
        super().__init__(
            label,
            left_hand_side,
            ast_node,
            right_hand_side_variables,
            line_number=ast_node.lineno,
            path=path
        )


class YieldNode(AssignmentNode):
    ##TODO
    pass
