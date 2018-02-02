# -*- coding: utf-8 -*-

"""Transport backend definition."""

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from modoboa.transport import backends


class RelayTransportBackend(backends.TransportBackend):
    """Relay backend class."""

    name = "relay"

    settings = (
        {"name": "target_host", "label": _("target host address"),
         "validator": "host_address"},
        {"name": "target_port", "label": _("target host port"),
         "type": "int", "default": 25},
        {"name": "verify_recipients", "label": _("verify recipients"),
         "type": "boolean", "required": False, "default": False},
    )

    def serialize(self, transport):
        """Make sure next_hop is set."""
        transport.next_hop = "[{}]:{}".format(
            transport._settings["relay_target_host"],
            transport._settings["relay_target_port"])


backends.manager.register_backend(RelayTransportBackend)
