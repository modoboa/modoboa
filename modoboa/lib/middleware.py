"""Custom middlewares."""

from django.utils.deprecation import MiddlewareMixin

from modoboa.lib import signals as lib_signals


class RequestCatcherMiddleware(MiddlewareMixin):
    """Simple middleware to store the current request."""

    def process_request(self, request):
        lib_signals.set_current_request(request)

    def process_response(self, request, response):
        """Empty store."""
        lib_signals.set_current_request(None)
        return response
