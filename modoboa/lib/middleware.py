"""Custom middlewares."""

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str

from rest_framework.settings import api_settings
from rest_framework.throttling import BaseThrottle

from modoboa.lib import signals as lib_signals
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.web_utils import _render_error


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


class TrustedProxyMiddleware(MiddlewareMixin):
    """Set REMOTE_ADDR to the client address reported by trusted proxies.

    X-Forwarded-For is client-controlled except for the NUM_PROXIES last
    entries, the address is picked as rate limits do.
    """

    def process_request(self, request):
        if api_settings.NUM_PROXIES:
            request.META["REMOTE_ADDR"] = BaseThrottle().get_ident(request)


class CommonExceptionCatcher(MiddlewareMixin):
    """Modoboa exceptions catcher."""

    def process_exception(self, request, exception):
        if not isinstance(exception, ModoboaException):
            return None

        if "/api/" in request.path:
            http_code = exception.http_code if exception.http_code else 500
            return JsonResponse({"error": str(exception)}, status=http_code)

        return _render_error(request, user_context={"error": smart_str(exception)})


class RequestCatcherMiddleware(MiddlewareMixin):
    """Simple middleware to store the current request."""

    def process_request(self, request):
        lib_signals.set_current_request(request)

    def process_response(self, request, response):
        """Empty store."""
        lib_signals.set_current_request(None)
        return response
