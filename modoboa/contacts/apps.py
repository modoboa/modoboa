"""AppConfig for contacts."""

from django.apps import AppConfig


class ModoboaContactsConfig(AppConfig):
    name = "modoboa.contacts"

    def ready(self):
        from . import handlers  # noqa
        from modoboa.contacts.app_settings import load_settings

        load_settings()
