"""AppConfig for stats."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy


def load_settings():
    from modoboa.parameters import tools as param_tools
    from . import app_settings
    from .api.v2 import serializers

    param_tools.registry.add(
        "global",
        "sievefilters",
        gettext_lazy("Sieve filters"),
        app_settings.SIEVEFILTERS_PARAMETERS_STRUCT,
        serializers.SievefiltersSettingsSerializer,
        False,
    )


class SieveFiltersConfig(AppConfig):
    """App configuration."""

    name = "modoboa.sievefilters"
    verbose_name = "Sieve filters editor for Modoboa"

    def ready(self):
        load_settings()
