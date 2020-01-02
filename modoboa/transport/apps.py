# -*- coding: utf-8 -*-

from django.apps import AppConfig


class TransportConfig(AppConfig):
    name = "modoboa.transport"

    def ready(self):
        from . import handlers  # NOQA:F401
