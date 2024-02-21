"""Custom middlewares."""

from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str

from modoboa.lib import signals as lib_signals
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.web_utils import _render_error, ajax_response, render_to_json_response


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


class AjaxLoginRedirect(MiddlewareMixin):

    def process_response(self, request, response):
        if is_ajax(request):
            if isinstance(response, HttpResponseRedirect):
                response.status_code = 278
        return response


class CommonExceptionCatcher(MiddlewareMixin):
    """Modoboa exceptions catcher."""

    def process_exception(self, request, exception):
        if not isinstance(exception, ModoboaException):
            return None

        if is_ajax(request) or "/api/" in request.path:
            if exception.http_code is None:
                return ajax_response(
                    request, status="ko", respmsg=smart_str(exception), norefresh=True
                )
            return render_to_json_response(
                smart_str(exception), status=exception.http_code
            )
        return _render_error(request, user_context={"error": smart_str(exception)})


class RequestCatcherMiddleware(MiddlewareMixin):
    """Simple middleware to store the current request."""

    def process_request(self, request):
        lib_signals.set_current_request(request)

    def process_response(self, request, response):
        """Empty store."""
        lib_signals.set_current_request(None)
        return response
