"""App config for limits."""

from django.apps import AppConfig
from django.utils.translation import gettext as _


def load_limits_settings():
    """Load settings."""
    from modoboa.parameters import tools as param_tools
    from . import app_settings
    from .api.v2 import serializers

    param_tools.registry.add("global", app_settings.ParametersForm, _("Limits"))
    param_tools.registry.add2(
        "global",
        "limits",
        _("Limits"),
        app_settings.GLOBAL_PARAMETERS_STRUCT,
        serializers.LimitsGlobalParemetersSerializer,
    )


class LimitsConfig(AppConfig):
    """App configuration."""

    name = "modoboa.limits"
    verbose_name = "Modoboa admin limits"

    def ready(self):
        load_limits_settings()

        from . import handlers  # NOQA:F401
