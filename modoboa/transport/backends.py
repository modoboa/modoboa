# -*- coding: utf-8 -*-

"""Transport backend."""

from __future__ import unicode_literals

from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from modoboa.lib import validators as lib_validators


class TransportBackend(object):
    """Base backend class."""

    name = None
    settings = ()

    def _validate_host_address(self, value):
        """Validate an host address syntax."""
        validator_list = [
            lib_validators.validate_hostname,
            validators.validate_ipv46_address
        ]
        for validator in validator_list:
            try:
                validator(value)
            except forms.ValidationError:
                pass
            else:
                return True
        return False

    def clean_fields(self, values):
        """Check that values are correct."""
        errors = []
        for setting in self.settings:
            fname = "{}_{}".format(self.name, setting["name"])
            value = values.get(fname)
            if not value:
                if not setting.get("required", True):
                    continue
                errors.append((fname, _("This field is required")))
                continue
            ftype = setting.get("type", "string")
            if ftype == "string":
                validator = setting.get("validator")
                vfunc = "_validate_{}".format(validator)
                if validator and hasattr(self, vfunc):
                    if getattr(self, vfunc)(value):
                        continue
                else:
                    continue
            elif ftype == "int" and isinstance(value, int):
                continue
            elif ftype == "boolean" and isinstance(value, bool):
                continue
            errors.append((fname, _("Invalid value")))
        return errors

    def serialize(self, transport):
        """Transform received values if needed."""
        pass


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
        return sorted(
            (
                (key, key)
                for key, backend in self.backends.items()
            ),
            key=lambda i: i[1]
        )

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
