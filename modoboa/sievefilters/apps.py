"""AppConfig for stats."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy


def load_settings():
    from modoboa.parameters import tools as param_tools
    from modoboa.sievefilters import forms
    from . import app_settings
    from .api.v2 import serializers

    # Admin parameters
    param_tools.registry.add(
        "global", forms.ParametersForm, gettext_lazy("Sieve filters")
    )
    param_tools.registry.add2(
        "global",
        "sievefilters",
        gettext_lazy("Sieve filters"),
        app_settings.SIEVEFILTERS_PARAMETERS_STRUCT,
        serializers.SievefiltersSettingsSerializer,
        False,
    )

    # User parameters
    param_tools.registry.add(
        "user", forms.UserSettings, gettext_lazy("Message filters")
    )


class SieveFiltersConfig(AppConfig):
    """App configuration."""

    name = "modoboa.sievefilters"
    verbose_name = "Sieve filters editor for Modoboa"

    def ready(self):
        load_settings()
