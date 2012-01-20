# -*- coding: utf-8 -*-

import re
from django.http import Http404, HttpResponseRedirect
from modoboa.admin.models import Extension
from modoboa.lib.webutils import _render_error, ajax_response
from modoboa.lib.exceptions import ModoboaException

class ExtControlMiddleware(object):
    def process_view(self, request, view, args, kwargs):
        m = re.match("modoboa\.extensions\.(\w+)", view.__module__)
        if m is None:
            return None
        ext = Extension.objects.get(name=m.group(1))
        if ext is None:
            return None
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
            return _render_error(request, errortpl="error_simple",
                                 user_context=dict(error=str(exception)))
        
        return ajax_response(request, status="ko", respmsg=str(exception))
