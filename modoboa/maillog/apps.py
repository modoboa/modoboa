"""AppConfig for stats."""

import collections

from django.apps import AppConfig
from django.utils.translation import gettext, gettext_lazy as _


GLOBAL_PARAMETERS_STRUCT = collections.OrderedDict(
    [
        (
            "general",
            {
                "label": _("General"),
                "params": collections.OrderedDict(
                    [
                        (
                            "logfile",
                            {
                                "label": _("Path to the log file"),
                                "help_text": _(
                                    "Path to log file used to collect statistics"
                                ),
                            },
                        ),
                        (
                            "rrd_rootdir",
                            {
                                "label": _("Directory to store RRD files"),
                                "help_text": _(
                                    "Path to directory where RRD files are stored"
                                ),
                            },
                        ),
                        (
                            "greylist",
                            {
                                "label": _("Show greylisted messages"),
                                "help_text": _(
                                    "Differentiate between hard and soft rejects (greylisting)"
                                ),
                            },
                        ),
                    ]
                ),
            },
        )
    ]
)


def load_maillog_settings():
    """Load app settings."""
    from modoboa.maillog import forms
    from modoboa.maillog.api.v2 import serializers
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add("global", forms.ParametersForm, gettext("Statistics"))
    param_tools.registry.add2(
        "global",
        "maillog",
        gettext("Statistics"),
        GLOBAL_PARAMETERS_STRUCT,
        serializers.MaillogGlobalParemetersSerializer,
    )


class MaillogConfig(AppConfig):
    """App configuration."""

    name = "modoboa.maillog"
    verbose_name = "Modoboa graphical statistics"

    def ready(self):
        load_maillog_settings()
        from . import handlers  # noqa
