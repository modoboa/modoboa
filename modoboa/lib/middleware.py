# coding: utf-8
"""
Custom middlewares.
"""
import re
from django.http import Http404, HttpResponseRedirect
from modoboa.core.models import Extension
from modoboa.core.extensions import exts_pool
from modoboa.lib.webutils import (
    _render_error, ajax_response, render_to_json_response
)
from modoboa.lib.exceptions import ModoboaException
from modoboa.lib.signals import request_accessor


class ExtControlMiddleware(object):
    def process_view(self, request, view, args, kwargs):
        m = re.match("modoboa\.extensions\.(\w+)", view.__module__)
        if m is None:
            return None
        try:
            ext = Extension.objects.get(name=m.group(1))
        except Extension.DoesNotExist:
            extdef = exts_pool.get_extension(m.group(1))
            if extdef.always_active:
                return None
            raise Http404
        if ext.enabled:
            return None
        raise Http404


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
