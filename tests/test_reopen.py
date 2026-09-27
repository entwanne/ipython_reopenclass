import textwrap

import IPython
import pytest


class Shell:
    def __init__(self):
        self.ipython = IPython.InteractiveShell()

    def run(self, cmd):
        result = self.ipython.run_cell(textwrap.dedent(cmd))
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
