# coding: utf-8

"""Custom middlewares."""

from django.http import HttpResponseRedirect

from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.signals import request_accessor
from modoboa.lib.web_utils import (
    _render_error, ajax_response, render_to_json_response
)

from . import singleton


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


class RequestCatcherMiddleware(singleton.Singleton):
    """Simple middleware to store the current request.

    FIXME: the Singleton hack is used to make tests work. I don't know
    why but middlewares are not dropped between test case runs so more
    than one instance can be listening to the request_accessor signal
    and we don't want that!
    """

    def __init__(self):
        self._request = None
        request_accessor.connect(self)

    def process_request(self, request):
        self._request = request

    def process_response(self, request, response):
        """Empty self._request."""
        self._request = None
        return response

    def __call__(self, **kwargs):
        return self._request
