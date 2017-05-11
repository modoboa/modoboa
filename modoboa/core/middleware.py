"""Core middlewares."""

from __future__ import unicode_literals

from . import models


class LocalConfigMiddleware(object):
    """A middleware to inject LocalConfig into request."""

    def process_request(self, request):
        """Inject LocalConfig instance to request."""
        request.localconfig = models.LocalConfig.objects.first()
