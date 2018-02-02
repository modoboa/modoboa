# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.apps import AppConfig


class TransportConfig(AppConfig):
    name = "modoboa.transport"

    def ready(self):
        from . import handlers  # NOQA:F401
