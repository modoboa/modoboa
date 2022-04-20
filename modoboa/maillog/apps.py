"""AppConfig for stats."""

from django.apps import AppConfig

from .forms import load_settings


class MaillogConfig(AppConfig):
    """App configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modoboa.maillog"
    verbose_name = "Modoboa graphical statistics"

    def ready(self):
        load_settings()
        from . import handlers
