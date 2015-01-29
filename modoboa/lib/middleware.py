# coding: utf-8

"""Custom middlewares."""

from django.http import HttpResponseRedirect

from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.signals import request_accessor
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

    def process_exception(self, request, exception):
        if not isinstance(exception, ModoboaException):
            return None

        if not request.is_ajax():
            return _render_error(
                request, user_context=dict(error=str(exception))
            )
        if exception.http_code is None:
            return ajax_response(
                request, status="ko", respmsg=unicode(exception), norefresh=True
            )
        return render_to_json_response(
            unicode(exception), status=exception.http_code
        )


class RequestCatcherMiddleware(object):

    """
    Simple middleware to store the current request.
    """

    def __init__(self):
        self._request = None
        request_accessor.connect(self)

    def process_request(self, request):
        self._request = request

    def __call__(self, **kwargs):
        return self._request
