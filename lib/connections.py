from modoboa.auth.lib import decrypt

class ConnectionsManager(type):
    """Singleton pattern implementation

    This class is specialized in connection management.
    """
    def __init__(cls, name, bases, dict):
        super(ConnectionsManager, cls).__init__(name, bases, dict)
        cls.instances = {}

    def __call__(cls, **kwargs):
        key = None
        if kwargs.has_key("user"):
            key = kwargs["user"]
        else:
            return None
        if not cls.instances.has_key(key):
            cls.instances[key] = None
        if kwargs.has_key("password"):
            kwargs["password"] = decrypt(kwargs["password"])

        if cls.instances[key] is None:
            cls.instances[key] = \
                super(ConnectionsManager, cls).__call__(**kwargs)
        else:
            cls.instances[key].refresh(key, kwargs["password"])
        return cls.instances[key]

class ConnectionError(Exception):
    pass
