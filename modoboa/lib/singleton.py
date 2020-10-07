# works in Python 2 & 3
class _Singleton(type):
    _instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self._instances:
            self._instances[self] = \
                super(_Singleton, self).__call__(*args, **kwargs)
        return self._instances[self]


class Singleton(_Singleton("SingletonMeta", (object,), {})):
    pass
