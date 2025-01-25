from django.apps import AppConfig


class ModoboaContactsConfig(AppConfig):
    name = "modoboa.contacts"

    def ready(self):
        from . import handlers
