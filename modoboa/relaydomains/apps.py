"""AppConfig for relaydomains."""

from django.apps import AppConfig


class RelayDomainsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.relaydomains"
    verbose_name = "Modoboa relay domains"

    def ready(self):
        from . import handlers
