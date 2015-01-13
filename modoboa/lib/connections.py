from modoboa.lib.cryptutils import decrypt


class ConnectionsManager(type):

    """
    Singleton pattern implementation.

    This class is specialized in connection management.
    """

    def __init__(cls, name, bases, ctx):
        super(ConnectionsManager, cls).__init__(name, bases, ctx)
        cls.instances = {}

    def __call__(cls, **kwargs):
        key = None
        if "user" in kwargs:
            key = kwargs["user"]
        else:
            return None
        if key not in cls.instances:
            cls.instances[key] = None
        if "password" in kwargs:
            kwargs["password"] = decrypt(kwargs["password"])

        if cls.instances[key] is None:
            cls.instances[key] = \
                super(ConnectionsManager, cls).__call__(**kwargs)
        else:
            cls.instances[key].refresh(key, kwargs["password"])
        return cls.instances[key]


class ConnectionError(Exception):
    pass
