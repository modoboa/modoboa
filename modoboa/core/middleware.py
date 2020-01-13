"""Core middlewares."""

from django.utils.deprecation import MiddlewareMixin

from . import models


class LocalConfigMiddleware(MiddlewareMixin):
    """A middleware to inject LocalConfig into request."""

    def process_request(self, request):
        """Inject LocalConfig instance to request."""
        request.localconfig = models.LocalConfig.objects.first()
