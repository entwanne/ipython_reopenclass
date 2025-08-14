# Reopenable classes

To use in IPython snippets / jupyter notebooks.

It allows to define a class in several `class` blocks, by allowing a class to be reopened.
To reopen a class, just define as a usual one but add `[...]` as first item of class body.

```python
class Foo:
    def spam(self):
        return 'test'

class Foo:
    [...]

    def __str__(self):
        return self.spam()

print(Foo())
```
