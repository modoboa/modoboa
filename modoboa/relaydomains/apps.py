"""AppConfig for relaydomains."""

from __future__ import unicode_literals

from django.apps import AppConfig


class RelayDomainsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.relaydomains"
    verbose_name = "Modoboa relay domains"

    def ready(self):
        from . import handlers
        from . import transport
