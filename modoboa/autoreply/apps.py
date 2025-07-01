"""AppConfig for modoboa_postfix_autoreply."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy


def load_settings():
    from modoboa.parameters import tools as param_tools
    from . import app_settings
    from .api.v2 import serializers

    param_tools.registry.add(
        "global",
        "autoreply",
        gettext_lazy("Automatic replies"),
        app_settings.AUTOREPLY_PARAMETERS_STRUCT,
        serializers.AutoreplySettingsSerializer,
        False,
    )


class AutoreplyConfig(AppConfig):
    """App configuration."""

    name = "modoboa.autoreply"
    verbose_name = "Auto-reply functionality"

    def ready(self):
        load_settings()
