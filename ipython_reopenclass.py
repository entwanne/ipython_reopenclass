import ast
import itertools

reopen_node, = ast.parse('[...]').body
ellipsis = ast.Constant(value=...)


class Reopener(ast.NodeTransformer):
    'Transformer that stores all cells to re-execute them when classes/functions are redefined'

    def __init__(self):
        self.classes = {}
        self.functions = {}
        self.links = {}

        self.replay = False
        self.replay_module = ast.Module()
        self.replay_rewriter = Rewriter(self.classes, self.functions)

    @staticmethod
    def _get_next_id(_seq=itertools.count(1)):
        return next(_seq)

    def visit_Module(self, node):
        self.replay = (node.body and ast.dump(node.body[0]) == ast.dump(reopen_node))
        self.append_nodes = []

        # Visit the nodes of the module (to register functions/classes if any)
        module = self.generic_visit(node)

        if self.replay:
            self.replay_module.body.extend(module.body)
            self.replay_module = self.replay_rewriter.visit(self.replay_module)
            module.body.clear()

        # Do not end with the expression of the replay_module
        end_body = []
        if self.append_nodes or self.replay_module.body:
            last_stmt = ast.Pass()
            ast.fix_missing_locations(last_stmt)
            end_body.append(last_stmt)

        # Still end the cell with the value of the last expression if any
        if module.body and isinstance(module.body[-1], ast.Expr) and (self.append_nodes or self.replay_module.body):
            output_name = f'__cell_output_{self._get_next_id()}'
            module.body[-1] = ast.Assign(
                targets=[ast.Name(id=output_name, ctx=ast.Store())],
                value=module.body[-1].value,
            )
            ast.fix_missing_locations(module.body[-1])
            last_value = ast.Expr(value=ast.Name(id=output_name))
            ast.fix_missing_locations(last_value)
            end_body.append(last_value)

        # Prepend the body of replay_module to all cells
        module.body = [
            *module.body,
            *self.append_nodes,
            *self.replay_module.body,
            *end_body,
        ]

        self.replay = False
        return module

    def visit_ClassDef(self, node):
        # Extend existing class definition if any
        reopened = False
        if existing_node := self.classes.get(node.name):
            if node.bases:
                if ast.dump(node.bases[0]) == ast.dump(ellipsis):
                    node.bases[:1] = existing_node.bases
                    reopened = True
            if node.body:
                if ast.dump(node.body[0]) == ast.dump(reopen_node):
                    node.body = existing_node.body + node.body
                    reopened = True

        # Register class to be reopened later
        self.classes[node.name] = node

        # Register links between parent and children classes
        for base in node.bases:
            base_name = ast.unparse(base)
            if base_name in self.classes:
                self.links.setdefault(base_name, set()).add(node.name)

        if reopened:
            # Redefine child-classes if parent one has been reopened
            for child in self.links.get(node.name, ()):
                if not (child_class := self.classes.get(child)):
                    continue
                self.append_nodes.append(child_class)

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
