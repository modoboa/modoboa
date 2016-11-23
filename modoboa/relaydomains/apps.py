"""AppConfig for relaydomains."""

from django.apps import AppConfig
from django.utils.translation import ugettext as _


def load_relaydomains_settings():
    """Load application settings."""
    from modoboa.parameters import tools as param_tools
    from .app_settings import AdminParametersForm

    param_tools.registry.add("global", AdminParametersForm, _("Relay domains"))


class RelayDomainsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.relaydomains"
    verbose_name = "Modoboa relay domains"

    def ready(self):
        load_relaydomains_settings()
        from . import handlers
