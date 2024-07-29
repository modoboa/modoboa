"""Sieve filters forms."""

import collections

from django.utils.translation import gettext_lazy as _

SIEVEFILTERS_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "manage_sieve_settings",
            {
                "label": _("ManageSieve settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "server",
                            {
                                "label": _("Server address"),
                                "help_text": _("Address of your MANAGESIEVE server"),
                            },
                        ),
                        (
                            "port",
                            {
                                "label": _("Server port"),
                                "help_text": _(
                                    "Listening port of your MANAGESIEVE server"
                                ),
                            },
                        ),
                        (
                            "starttls",
                            {
                                "label": _("Connect using STARTTLS"),
                                "help_text": _("Use the STARTTLS extension"),
                            },
                        ),
                    ]
                ),
            },
        ),
        (
            "imap_settings",
            {
                "label": _("IMAP settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "imap_server",
                            {
                                "label": _("Server address"),
                                "help_text": _("Address of your IMAP server"),
                            },
                        ),
                        (
                            "imap_secured",
                            {
                                "label": _("Use a secured connection"),
                                "help_text": _(
                                    "Use a secured connection to access IMAP server"
                                ),
                            },
                        ),
                        (
                            "imap_port",
                            {
                                "label": _("Server port"),
                                "help_text": _("Listening port of your IMAP server"),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
