import ast

reopen_node, = ast.parse('[...]').body
ellipsis = ast.Constant(value=...)


class Reopener(ast.NodeTransformer):
    'Transformer that stores all cells to re-execute them when classes/functions are redefined'

    def __init__(self):
        self.classes = {}
        self.functions = {}

        self.replay = False
        self.replay_module = ast.Module()
        self.replay_rewriter = Rewriter(self.classes, self.functions)

    def visit_Module(self, node):
        self.replay = (node.body and ast.dump(node.body[0]) == ast.dump(reopen_node))
        # Visit the nodes of the module (to register functions/classes if any)
        module = self.generic_visit(node)
        if self.replay:
            self.replay_module.body.extend(module.body)
            self.replay_module = self.replay_rewriter.visit(self.replay_module)
            module.body.clear()
        # Prepend the body of replay_module to all cells
        module.body = [*module.body, *self.replay_module.body]
        self.replay = False
        return module

    def visit_ClassDef(self, node):
        # Extend existing class definition if any
        if existing_node := self.classes.get(node.name):
            if node.bases:
                if ast.dump(node.bases[0]) == ast.dump(ellipsis):
                    node.bases[:1] = existing_node.bases
            if node.body:
                if ast.dump(node.body[0]) == ast.dump(reopen_node):
                    node.body = existing_node.body + node.body
        self.classes[node.name] = node
        if self.replay and existing_node:
            # returns None because replay_module already contains the definition
            # so we don't want to duplicate it
            return None
        return node

    def visit_FunctionDef(self, node):
        # Replace existing function definition if any
        existing_node = self.functions.get(node.name)
        self.functions[node.name] = node
        if self.replay and existing_node:
            # returns None because replay_module already contains the definition
            # so we don't want to duplicate it
            return None
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


class Extension:
    def __init__(self):
        self.visitor = Reopener()
        self.transformers = []

    def load(self, ipython):
        self.transformers = ipython.ast_transformers.copy()
        ipython.ast_transformers.append(self.visitor)

    def unload(self, ipython):
        ipython.ast_transformers[:] = self.transformers
        self.transformers.clear()


extension = None


def load_ipython_extension(ipython):
    global extension
    extension = Extension()
    extension.load(ipython)


def unload_ipython_extension(ipython):
    global extension
    if extension is not None:
        extension.unload(ipython)
        extension = None
