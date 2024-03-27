"""AppConfig for stats."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy


def load_settings():
    from modoboa.parameters import tools as param_tools
    from modoboa.sievefilters import forms

    param_tools.registry.add(
        "global", forms.ParametersForm, gettext_lazy("Sieve filters")
    )
    param_tools.registry.add(
        "user", forms.UserSettings, gettext_lazy("Message filters")
    )


class SieveFiltersConfig(AppConfig):
    """App configuration."""

    name = "modoboa.sievefilters"
    verbose_name = "Sieve filters editor for Modoboa"

    def ready(self):
        load_settings()
        from . import handlers
