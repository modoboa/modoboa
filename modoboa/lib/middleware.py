# coding: utf-8

"""Custom middlewares."""

from django.http import HttpResponseRedirect

from modoboa.lib.exceptions import ModoboaException
from modoboa.lib import signals as lib_signals
from modoboa.lib.web_utils import (
    _render_error, ajax_response, render_to_json_response
)


class AjaxLoginRedirect(object):

    def process_response(self, request, response):
        if request.is_ajax():
            if type(response) == HttpResponseRedirect:
                response.status_code = 278
        return response


class CommonExceptionCatcher(object):
    """Modoboa exceptions catcher."""

    def process_exception(self, request, exception):
        if not isinstance(exception, ModoboaException):
            return None

        if request.is_ajax() or "/api/" in request.path:
            if exception.http_code is None:
                return ajax_response(
                    request, status="ko", respmsg=unicode(exception),
                    norefresh=True
                )
            return render_to_json_response(
                unicode(exception), status=exception.http_code
            )
        return _render_error(
            request, user_context=dict(error=str(exception))
        )


class RequestCatcherMiddleware(object):
    """Simple middleware to store the current request."""

    def process_request(self, request):
        lib_signals.set_current_request(request)

    def process_response(self, request, response):
        """Empty store."""
        lib_signals.set_current_request(None)
        return response
