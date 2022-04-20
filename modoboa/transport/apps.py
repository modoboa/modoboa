from django.apps import AppConfig


class TransportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modoboa.transport"

    def ready(self):
        from . import handlers  # NOQA:F401
