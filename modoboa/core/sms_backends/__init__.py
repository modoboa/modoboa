"""SMS backends."""

from importlib import import_module

from .. import constants


class SMSBackend:
    """Base class of every SMS backend."""

    settings = {}
    visibility_rules = {}

    def __init__(self, params):
        """Default constructor."""
        self._params = params

    def send(self, text, recipients):
        """Send a new SMS to given recipients."""
        raise NotImplementedError


def get_backend_class(name):
    """Return class for given backend."""
    backend_module = import_module(
        "modoboa.core.sms_backends.{}".format(name))
    try:
        backend_class = getattr(
            backend_module, "{}Backend".format(name.upper()))
    except AttributeError:
        return None
    else:
        return backend_class


def get_backend_settings(name):
    """Return settings of given backend."""
    backend_class = get_backend_class(name)
    if not backend_class:
        return None
    return backend_class.settings


def get_all_backend_settings():
    """Return settings of all backends."""
    settings = {}
    for backend in constants.SMS_BACKENDS:
        name = backend[0]
        if not name:
            continue
        b_settings = get_backend_settings(name)
        if b_settings:
            settings.update(b_settings)
    return settings


def get_all_backend_visibility_rules():
    """Return visibility rules of all backends."""
    rules = {}
    for backend in constants.SMS_BACKENDS:
        name = backend[0]
        if not name:
            continue
        backend_class = get_backend_class(name)
        if not backend_class:
            continue
        rules.update(backend_class.visibility_rules)
    return rules


def get_active_backend(parameters):
    """Return active SMS backend."""
    name = parameters.get_value("sms_provider")
    if not name:
        return None
    backend_class = get_backend_class(name)
    if not backend_class:
        return None
    return backend_class(parameters)
