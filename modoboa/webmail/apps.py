"""AppConfig for webmail."""

from django.apps import AppConfig


class WebmailConfig(AppConfig):
    """App configuration."""

    name = "modoboa.webmail"
    verbose_name = "Modoboa webmail"

    def ready(self):
        from modoboa.webmail.app_settings import load_settings

        load_settings()
