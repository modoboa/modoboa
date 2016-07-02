"""AppConfig for relaydomains."""

from django.apps import AppConfig


EVENTS = [
    "RelayDomainCreated",
    "RelayDomainDeleted",
    "RelayDomainModified",
    "RelayDomainAliasCreated",
    "RelayDomainAliasDeleted",
    "ExtraRelayDomainForm",
    "FillRelayDomainInstances"
]


def load_relaydomains_settings():
    """Load application settings."""
    from django.utils.translation import ugettext as _
    from modoboa.lib import events, parameters
    from .app_settings import AdminParametersForm

    parameters.register(AdminParametersForm, _("Relay domains"))
    events.declare(EVENTS)
    from . import general_callbacks


class RelayDomainsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.relaydomains"
    verbose_name = "Modoboa relay domains"

    def ready(self):
        load_relaydomains_settings()
        from . import handlers
