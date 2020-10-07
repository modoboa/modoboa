from modoboa.lib.cryptutils import decrypt


class ConnectionsManager(type):

    """
    Singleton pattern implementation.

    This class is specialized in connection management.
    """

    def __init__(self, name, bases, ctx):
        super(ConnectionsManager, self).__init__(name, bases, ctx)
        self.instances = {}

    def __call__(self, **kwargs):
        key = None
        if "user" in kwargs:
            key = kwargs["user"]
        else:
            return None
        if key not in self.instances:
            self.instances[key] = None
        if "password" in kwargs:
            kwargs["password"] = decrypt(kwargs["password"])

        if self.instances[key] is None:
            self.instances[key] = \
                super(ConnectionsManager, self).__call__(**kwargs)
        else:
            self.instances[key].refresh(key, kwargs["password"])
        return self.instances[key]


class ConnectionError(Exception):
    pass
