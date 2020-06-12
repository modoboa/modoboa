"""AppConfig for policyd."""

from django.apps import AppConfig


class PolicydConfig(AppConfig):
    """App configuration."""

    name = "modoboa.policyd"
    verbose_name = "Modoboa policy daemon"

    def ready(self):
        from . import handlers  # NOQA:F401
