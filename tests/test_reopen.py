import textwrap

import IPython
import pytest


class Shell:
    def __init__(self):
        self.ipython = IPython.InteractiveShell()

    def run(self, cmd, **meta):
        result = self.ipython.run_cell(textwrap.dedent(cmd), cell_meta=meta)
        assert not result.error_in_exec

    def __getitem__(self, name):
        return self.ipython.ns_table['user_local'][name]


@pytest.fixture()
def shell():
    sh = Shell()
    sh.run('%load_ext ipython_reopenclass')
    return sh


def test_reopen(shell):
    shell.run('''
    class A:
        def foo(self):
            return 'foo1'

        def bar(self):
            return 'bar1'

    obj = A()
    ''')

    cls = shell['A']
    obj = shell['obj']

    assert cls.__name__ == 'A'
    assert cls.__bases__ == (object,)

    assert isinstance(obj, cls)
    assert obj.foo() == 'foo1'
    assert obj.bar() == 'bar1'

    shell.run('''
    class A:
        [...]

        def bar(self):
            return 'bar2'

        def baz(self):
            return 'baz2'

    obj2 = A()
    ''')

    cls2 = shell['A']
    obj2 = shell['obj2']

    assert cls2 is not cls
    assert cls2.__name__ == 'A'
    assert cls2.__bases__ == (object,)

    assert isinstance(obj2, cls2)
    assert not isinstance(obj2, cls)

    assert shell['obj'] is obj
    assert not isinstance(obj, cls2)

    assert obj2.foo() == 'foo1'
    assert obj2.bar() == 'bar2'
    assert obj2.baz() == 'baz2'
    assert obj.bar() == 'bar1'


def test_subclasses(shell):
    shell.run('''
    class B(int):
        pass

    class B():
        [...]
    ''')
    assert shell['B'].__bases__ == (object,)

    shell.run('''
    class C(int):
        pass

    class C(...):
        pass
    ''')
    assert shell['C'].__bases__ == (int,)


def test_replay(shell):
    shell.run('''
    class A:
        name = 'A'
        foo = 'foo1'
    ''', replay=True)

    shell.run('obj1 = A()')
    shell.run('obj2 = A()', replay=True)

    assert shell['obj1'].name == 'A'
    assert shell['obj1'].foo == 'foo1'
    assert shell['obj2'].foo == 'foo1'

    shell.run('''
    class A:
        [...]
        foo = 'foo2'
    obj3 = A()
    ''')

    assert shell['obj1'].foo == 'foo1'
    assert shell['obj2'].foo == 'foo1'
    assert shell['obj3'].name == 'A'
    assert shell['obj3'].foo == 'foo2'

    shell.run('''
    class A:
        [...]
        foo = 'foo3'
    obj4 = A()
    ''', replay=True)

    assert shell['obj1'].foo == 'foo1'
    assert shell['obj2'].foo == 'foo3'
    assert shell['obj3'].foo == 'foo2'
    assert shell['obj4'].name == 'A'
    assert shell['obj4'].foo == 'foo3'

    shell.run('''
    class A:
        pass
    obj5 = A()
    ''')

    assert shell['obj1'].foo == 'foo1'
    assert shell['obj2'].foo == 'foo3'
    assert shell['obj3'].foo == 'foo2'
    assert shell['obj4'].foo == 'foo3'
    assert not hasattr(shell['obj5'], 'foo')

    shell.run('''
    class A:
        pass
    obj6 = A()
    ''', replay=True)

    assert shell['obj1'].foo == 'foo1'
    assert not hasattr(shell['obj2'], 'foo')
    assert shell['obj3'].foo == 'foo2'
    assert not hasattr(shell['obj4'], 'foo')
    assert not hasattr(shell['obj5'], 'foo')
    assert not hasattr(shell['obj6'], 'foo')
