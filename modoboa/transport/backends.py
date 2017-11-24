"""Transport backend."""

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from modoboa.lib import validators as lib_validators


class TransportBackend(object):
    """Base backend class."""

    name = None
    settings = ()

    def clean_fields(self, values):
        """Clean received values."""
        return []

    def serialize(self, transport):
        """Make sure values are correct."""
        pass


class RelayTransportBackend(TransportBackend):
    """Relay backend class."""

    name = "relay"

    settings = (
        {"name": "target_host", "label": _("target host address")},
        {"name": "target_port", "label": _("target host port"),
         "default": "25"},
        {"name": "verify_recipients", "label": _("verify recipients"),
         "type": "boolean", "required": False},
    )

    def clean_fields(self, values):
        """Check that values are correct."""
        validator_list = [
            lib_validators.validate_hostname,
            validators.validate_ipv46_address
        ]
        value = values.get("relay_target_host")
        if not value:
            return [("relay_target_host", _("This field is required"))]
        for validator in validator_list:
            try:
                validator(value)
            except forms.ValidationError:
                pass
            else:
                return []
        return [("relay_target_host", _("Invalid value"))]

    def serialize(self, transport):
        """Make sure next_hop is set."""
        transport.next_hop = "[{}]:{}".format(
            transport._settings["relay_target_host"],
            transport._settings["relay_target_port"])


class TransportBackendManager(object):
    """Transport backends manager."""

    def __init__(self):
        """Constructor."""
        self.backends = {}

    def get_backend(self, name, **kwargs):
        """Return backend instance."""
        backend_class = self.backends.get(name)
        if backend_class is None:
            return None
        return backend_class(**kwargs)

    def get_backend_list(self):
        """Return known backend list."""
        return sorted([
            (key, key)
            for key, backend in self.backends.items()
        ], key=lambda i: i[1])

    def get_backend_settings(self, name):
        """Return backend settings."""
        backend_class = self.backends.get(name)
        if backend_class is None:
            return None
        return backend_class.settings

    def get_all_backend_settings(self):
        """Return all backend settings."""
        return {
            name: backend_class.settings
            for name, backend_class in list(self.backends.items())
        }

    def register_backend(self, backend_class):
        """Register a new backend."""
        if not backend_class.name:
            raise RuntimeError("missing backend name")
        self.backends[backend_class.name] = backend_class


manager = TransportBackendManager()
manager.register_backend(RelayTransportBackend)
