"""Transport handlers."""

from __future__ import unicode_literals

from django.urls import reverse
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from modoboa.admin import signals as admin_signals
from modoboa.core import signals as core_signals

from . import postfix_maps


@receiver(admin_signals.extra_domain_menu_entries)
def extra_domain_menu_entries(sender, user, **kwargs):
    """Add extra menu entries."""
    return [{
        "name": "transports",
        "label": _("Transports"),
        "url": reverse("transport:transport_list"),
        "img": "fa fa-bus",
    }]


@receiver(core_signals.register_postfix_maps)
def register_postfix_maps(sender, **kwargs):
    """Register postfix maps."""
    return [
        postfix_maps.TransportMap,
    ]
