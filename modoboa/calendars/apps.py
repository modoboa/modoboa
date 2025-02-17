"""AppConfig for radicale."""

from django.apps import AppConfig


class CalendarsConfig(AppConfig):
    """App configuration."""

    name = "modoboa.calendars"
    verbose_name = "Modoboa calendars"

    def ready(self):
        from modoboa.calendars import handlers  # noqa
        from modoboa.calendars.app_settings import load_settings

        load_settings()
