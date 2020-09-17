"""AppConfig for stats."""

from django.apps import AppConfig

from .forms import load_settings


class MaillogConfig(AppConfig):
    """App configuration."""

    name = "modoboa.maillog"
    verbose_name = "Modoboa graphical statistics"

    def ready(self):
        load_settings()
        from . import handlers
