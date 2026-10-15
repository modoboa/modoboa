"""Sieve filters settings."""

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
                                "help_text": _(
                                    "Use the STARTTLS extension. Without it, "
                                    "credentials are sent in clear, which is "
                                    "only acceptable when the server is local"
                                ),
                            },
                        ),
                    ]
                ),
            },
        ),
    ]
)
