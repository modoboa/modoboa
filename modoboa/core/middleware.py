# -*- coding: utf-8 -*-

"""Core middlewares."""

from __future__ import unicode_literals

from django.utils.deprecation import MiddlewareMixin

from . import models


class LocalConfigMiddleware(MiddlewareMixin):
    """A middleware to inject LocalConfig into request."""

    def process_request(self, request):
        """Inject LocalConfig instance to request."""
        request.localconfig = models.LocalConfig.objects.first()
