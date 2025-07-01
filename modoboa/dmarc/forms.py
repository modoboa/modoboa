"""Custom forms."""

import collections

from django.utils.translation import gettext_lazy as _

from modoboa.dmarc.api.v2 import serializers


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "dns",
            {
                "label": _("DNS settings"),
                "params": collections.OrderedDict(
                    [
                        (
                            "enable_rlookups",
                            {
                                "label": _("Enable reverse lookups"),
                                "help_text": _(
                                    "Enable reverse DNS lookups (reports will be longer to display)"
                                ),
                            },
                        )
                    ]
                ),
            },
        )
    ]
)


def load_settings():
    """Load app settings."""
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add(
        "global",
        "dmarc",
        _("DMARC"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.DmarcGlobalParametersSerializer,
        True,
    )
