import ast

reopen_node, = ast.parse('[...]').body
_classes = {}


def register_class(name, bases, dict):
    cls = type(name, bases, dict)
    _classes[cls.__module__, cls.__name__] = cls
    return cls


def reopen_class(name, bases, dict):
    base = _classes.get((dict.get('__module__'), name))
    if base is not None:
        bases += (base,)

    return register_class(name, bases, dict)


class ClassWrapper(ast.NodeTransformer):
    def visit_ClassDef(self, node):
        node.keywords.append(ast.keyword(
            arg='metaclass',
            value=ast.Name(
                id=(
                    'reopen_class'
                    if node.body and ast.dump(node.body[0]) == ast.dump(reopen_node)
                    else 'register_class'
                ),
                ctx=ast.Load(),
            ),
        ))
        return node


def load_ipython_extension(ipython):
    ipython.push({'register_class': register_class, 'reopen_class': reopen_class})
    ipython.ast_transformers.append(ClassWrapper())


def unload_ipython_extension(ipython):
    ipython.ast_transformers.clear()
