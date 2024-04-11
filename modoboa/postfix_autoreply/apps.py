"""AppConfig for modoboa_postfix_autoreply."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy


def load_settings():
    from modoboa.parameters import tools as param_tools
    from modoboa.postfix_autoreply import forms

    param_tools.registry.add(
        "global", forms.ParametersForm, gettext_lazy("Automatic replies")
    )


class PostfixAutoreplyConfig(AppConfig):
    """App configuration."""

    name = "modoboa.postfix_autoreply"
    verbose_name = "Auto-reply functionality using Postfix"

    def ready(self):
        load_settings()
        from . import handlers  # NOQA:F401
