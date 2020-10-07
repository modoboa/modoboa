from django.apps import AppConfig


class LdapsyncConfig(AppConfig):
    name = 'modoboa.ldapsync'

    def ready(self):
        from . import handlers  # noqa
