"""AppConfig for amavis."""

from django.apps import AppConfig


class AmavisConfig(AppConfig):
    """App configuration."""

    name = "modoboa.amavis"
    verbose_name = "Modoboa amavis frontend"

    def ready(self):
        # Import these to force registration of checks and signals
        from . import checks  # NOQA:F401
        from . import handlers  # NOQA:F401
        from modoboa.amavis.app_settings import load_settings

        load_settings()
