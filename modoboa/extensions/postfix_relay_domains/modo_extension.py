# coding: utf-8

"""Declare postfix_relay_domains extension and register it."""

from django.utils.translation import ugettext_lazy

from modoboa.core.extensions import ModoExtension, exts_pool
from modoboa.lib import events, parameters


EXTENSION_EVENTS = [
    "RelayDomainCreated",
    "RelayDomainDeleted",
    "RelayDomainModified",
    "RelayDomainAliasCreated",
    "RelayDomainAliasDeleted",
    "ExtraRelayDomainForm",
    "FillRelayDomainInstances"
]


class PostfixRelayDomains(ModoExtension):

    """Extension declaration."""

    name = "postfix_relay_domains"
    label = "Postfix relay domains"
    version = "1.0"
    description = ugettext_lazy("Relay domains support for Postfix")

    def load(self):
        from .app_settings import AdminParametersForm

        parameters.register(
            AdminParametersForm, ugettext_lazy("Relay domains")
        )
        events.declare(EXTENSION_EVENTS)
        from modoboa.extensions.postfix_relay_domains import general_callbacks
        if exts_pool.is_extension_installed("modoboa.extensions.limits"):
            import limits_callbacks
        if exts_pool.is_extension_installed("modoboa.extensions.amavis"):
            import amavis_callbacks

    def load_initial_data(self):
        """Create extension data."""
        from .models import Service
        for service_name in ['relay', 'smtp']:
            Service.objects.get_or_create(name=service_name)

        if not exts_pool.is_extension_installed("modoboa.extensions.limits"):
            return
        from .limits_callbacks import create_new_limits
        create_new_limits()

exts_pool.register_extension(PostfixRelayDomains)
