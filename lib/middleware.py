# -*- coding: utf-8 -*-

import re
from django.http import Http404
from modoboa.admin.models import Extension

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
