# -*- coding: utf-8 -*-

"""Custom middlewares."""

from __future__ import unicode_literals

from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_text

from modoboa.lib import signals as lib_signals
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.web_utils import (
    _render_error, ajax_response, render_to_json_response
)


class AjaxLoginRedirect(MiddlewareMixin):

    def process_response(self, request, response):
        if request.is_ajax():
            if isinstance(response, HttpResponseRedirect):
                response.status_code = 278
        return response


class CommonExceptionCatcher(MiddlewareMixin):
    """Modoboa exceptions catcher."""

    def process_exception(self, request, exception):
        if not isinstance(exception, ModoboaException):
            return None

        if request.is_ajax() or "/api/" in request.path:
            if exception.http_code is None:
                return ajax_response(
                    request, status="ko", respmsg=smart_text(exception),
                    norefresh=True
                )
            return render_to_json_response(
                smart_text(exception), status=exception.http_code
            )
        return _render_error(
            request, user_context={"error": smart_text(exception)}
        )


class RequestCatcherMiddleware(MiddlewareMixin):
    """Simple middleware to store the current request."""

    def process_request(self, request):
        lib_signals.set_current_request(request)

    def process_response(self, request, response):
        """Empty store."""
        lib_signals.set_current_request(None)
        return response
