"""App config for limits."""

from django.apps import AppConfig


EVENTS = [
    'GetExtraLimitTemplates'
]


def load_limits_settings():
    """Load settings."""
    from django.utils.translation import ugettext as _
    from modoboa.lib import events, parameters
    from .app_settings import ParametersForm

    parameters.register(ParametersForm, _("Limits"))
    events.declare(EVENTS)
    from . import controls
    from . import general_callbacks


class LimitsConfig(AppConfig):

    """App configuration."""

    name = "modoboa.limits"
    verbose_name = "Modoboa admin limits"

    def ready(self):
        load_limits_settings()

        from . import handlers
