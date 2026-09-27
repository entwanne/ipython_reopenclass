import ast

reopen_node, = ast.parse('[...]').body
ellipsis = ast.Constant(value=...)


class ModuleAggregator(ast.NodeTransformer):
    'Transformer that stores all cells to re-execute them when classes/functions are redefined'

    def __init__(self):
        self.base_module = ast.Module()
        self.classes = {}
        self.functions = {}
        self.rewriter = Rewriter(self.classes, self.functions)

    def visit_Module(self, node):
        module = self.generic_visit(node)
        self.base_module.body.extend(module.body)
        self.base_module = self.rewriter.visit(self.base_module)
        return self.base_module

    def visit_ClassDef(self, node):
        # Extend existing class definition if any
        # (returns None because base_module already contains the definition)
        if node.name in self.classes:
            if node.bases:
                if ast.dump(node.bases[0]) == ast.dump(ellipsis):
                    node.bases[:1] = self.classes[node.name].bases
            if node.body:
                if ast.dump(node.body[0]) == ast.dump(reopen_node):
                    node.body = self.classes[node.name].body + node.body
            self.classes[node.name] = node
            return None
        else:
            self.classes[node.name] = node
            return node

    def visit_FunctionDef(self, node):
        # Replace existing function definition if any
        # (returns None because base_module already contains the definition)
        if node.name in self.functions:
            self.functions[node.name] = node
            return None
        else:
            self.functions[node.name] = node
            return node


class Rewriter(ast.NodeTransformer):
    'Sub-transformer to be used to replace class/function definitions at the right place'
    def __init__(self, classes, functions):
        self.classes = classes
        self.functions = functions

    def visit_ClassDef(self, node):
        if node.name in self.classes:
            return self.classes[node.name]
        return node

    def visit_FunctionDef(self, node):
        if node.name in self.functions:
            return self.functions[node.name]
        return node


def load_ipython_extension(ipython):
    ipython.ast_transformers.append(ModuleAggregator())


def unload_ipython_extension(ipython):
    ipython.ast_transformers.clear()
