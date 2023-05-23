from simple_cfg.visitors.expression_visitor import ExprVisitor
from simple_cfg.translate.transformer import CFGTransformer

class CFG():
    def __init__(
        self,
        nodes,
        blackbox_assignments,
        filename
    ):
        #logging.info("CFG::nodes: ", nodes)
        self.nodes = nodes
        self.blackbox_assignments = blackbox_assignments
        self.filename = filename

    def __repr__(self):
        output = ''
        for x, n in enumerate(self.nodes):
            output = ''.join((output, 'Node: ' + str(x) + ' ' + repr(n), '\n\n'))
        return output

    def __str__(self):
        output = ''
        for x, n in enumerate(self.nodes):
            output = ''.join((output, 'Node: ' + str(x) + ' ' + str(n), '\n\n'))
        return output


def get_cfg(
    tree,
    filename,
    project_modules=None,
    local_modules=None,
    module_definitions=None,
    allow_local_directory_imports=True
):
    #logging.info("tree: ",
    #  tree)
    transformed_tree = CFGTransformer().visit(tree)
    visitor = ExprVisitor(
        transformed_tree,
        filename,
        project_modules=None,
        local_modules=None,
        module_definitions=None,
        allow_local_directory_imports=False
    )
    #logging.info("visitor.nodes: ", visitor.nodes)
    return CFG(
        visitor.nodes,
        visitor.blackbox_assignments,
        filename
    )

def edit_cfg(cfg):
    for iNode, node in enumerate(cfg.nodes):
        # Extract original node label from cfg
        nodeLabel = node.label # ex. 'df1.iloc[2] = df2.iloc[5]'
        if nodeLabel.count('=') <= 0:
            continue
        # Split node label into distinct LHS and RHS operands
        split_LHS_RHS = [x.strip() for x in nodeLabel.split('=')] # ex. [['df1.iloc[2]'], ['df2.iloc[5]']]
        assert(len(split_LHS_RHS) == 2)
        LHS = split_LHS_RHS[0] # ex. ['df1.iloc[2]']
        if (not isinstance(LHS, list)):
            LHS = [LHS]
        RHS = split_LHS_RHS[1] # ex. ['df2.iloc[5]']
        if (not isinstance(RHS, list)):
            RHS = [RHS]
        # Iterate over LHS operands for possible 'iloc' occurences
        for i, L in enumerate(LHS):
            if (L.count('iloc') > 0):
                before_ilocRange = L[:L.find('.iloc[')+6]
                after_ilocRange = L[L.find('.iloc[')+6:]
                # iloc indexes (from ast_node)
                ilocRowLower = str(cfg.nodes[iNode].targets[i].slice.dims[0].lower.n) if\
                cfg.nodes[iNode].targets[i].slice.dims[0].lower is not None else ':'
                ilocRowUpper = str(cfg.nodes[iNode].targets[i].slice.dims[0].upper.n) if\
                cfg.nodes[iNode].targets[i].slice.dims[0].upper is not None else ':'
                ilocColLower = str(cfg.nodes[iNode].targets[i].slice.dims[1].lower.n) if\
                cfg.nodes[iNode].targets[i].slice.dims[1].lower is not None else ':'
                ilocColUpper = str(cfg.nodes[iNode].targets[i].slice.dims[1].upper.n) if\
                cfg.nodes[iNode].targets[i].slice.dims[1].upper is not None else ':'
                # final operand expression
                LHS[i] = before_ilocRange + ilocRowLower + ilocRowUpper + ilocColLower +\
                    ilocColUpper + after_ilocRange[after_ilocRange.find(']'):]
    return cfg