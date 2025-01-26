"""AppConfig for contacts."""

from django.apps import AppConfig
from django.utils.translation import gettext

from modoboa.contacts.forms import UserSettings


def load_settings():
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add("user", UserSettings, gettext("Contacts"))


class ModoboaContactsConfig(AppConfig):
    name = "modoboa.contacts"

    def ready(self):
        from . import handlers

        load_settings()
