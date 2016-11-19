"""App config for limits."""

from django.apps import AppConfig
from django.utils.translation import ugettext as _

EVENTS = [
    "GetExtraLimitTemplates"
]


def load_limits_settings():
    """Load settings."""
    from modoboa.lib import events
    from modoboa.parameters import tools as param_tools
    from .app_settings import ParametersForm

    param_tools.registry.add("global", ParametersForm, _("Limits"))
    events.declare(EVENTS)
    from . import general_callbacks


class LimitsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.limits"
    verbose_name = "Modoboa admin limits"

    def ready(self):
        load_limits_settings()

        from . import handlers
