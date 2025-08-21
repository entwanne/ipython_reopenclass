import ast

reopen_node, = ast.parse('[...]').body
ellipsis = ast.Constant(value=...)
_class_bases = {}
_class_defs = {}


class ClassWrapper(ast.NodeTransformer):
    def visit_ClassDef(self, node):
        if node.bases:
            if ast.dump(node.bases[0]) == ast.dump(ellipsis):
                node.bases[:1] = _class_bases.get(node.name, [])
            _class_bases[node.name] = node.bases
        if node.body:
            if ast.dump(node.body[0]) == ast.dump(reopen_node):
                node.body = _class_defs.get(node.name, []) + node.body
            _class_defs[node.name] = node.body
        return node


def load_ipython_extension(ipython):
    ipython.ast_transformers.append(ClassWrapper())


def unload_ipython_extension(ipython):
    ipython.ast_transformers.clear()
