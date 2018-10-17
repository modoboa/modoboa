# -*- coding: utf-8 -*-

"""
This module contains extra functions/shortcuts used to render HTML.
"""

from __future__ import unicode_literals

import json
import re
import sys

from django import template
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def _render_error(request, errortpl="error", user_context=None):
    if user_context is None:
        user_context = {}
    return render(
        request, "common/%s.html" % errortpl, user_context
    )


def render_actions(actions):
    t = template.Template("""{% load lib_tags %}
{% for a in actions %}{% render_link a %}{% endfor %}
""")
    return t.render(template.Context({"actions": actions}))


def getctx(status, level=1, callback=None, **kwargs):
    if not callback:
        callername = sys._getframe(level).f_code.co_name
    else:
        callername = callback
    ctx = {"status": status, "callback": callername}
    for kw, v in list(kwargs.items()):
        ctx[kw] = v
    return ctx


def ajax_response(request, status="ok", respmsg=None,
                  url=None, ajaxnav=False, norefresh=False,
                  template=None, **kwargs):
    """Ajax response shortcut

    Simple shortcut that sends an JSON response. If a template is
    provided, a 'content' field will be added to the response,
    containing the result of this template rendering.

    :param request: a Request object
    :param status: the response status ('ok' or 'ko)
    :param respmsg: the message that will displayed in the interface
    :param url: url to display after receiving this response
    :param ajaxnav:
    :param norefresh: do not refresh the page after receiving this response
    :param template: eventual template's path
    :param kwargs: dict used for template rendering
    """
    ctx = {}
    for k, v in list(kwargs.items()):
        ctx[k] = v
    if template is not None:
        content = render_to_string(template, ctx, request)
    elif "content" in kwargs:
        content = kwargs["content"]
    else:
        content = ""
    jsonctx = {"status": status, "content": content}
    if respmsg is not None:
        jsonctx["respmsg"] = respmsg
    if ajaxnav:
        jsonctx["ajaxnav"] = True
    if url is not None:
        jsonctx["url"] = url
    jsonctx["norefresh"] = norefresh
    return JsonResponse(jsonctx)


def render_to_json_response(context, **response_kwargs):
    """Simple shortcut to render a JSON response.

    :param dict context: response content
    :return: ``HttpResponse`` object
    """
    data = json.dumps(context)
    response_kwargs["content_type"] = "application/json"
    return HttpResponse(data, **response_kwargs)


def static_url(path):
    """Returns the correct static url for a given file

    :param path: the targeted static media
    """
    if path.startswith("/"):
        path = path[1:]
    return "%s%s" % (settings.STATIC_URL, path)


def size2integer(value, output_unit="B"):
    """Try to convert a string representing a size to an integer value
    in bytes or megabytes.

    Supported formats:
    * K|k for KB
    * M|m for MB
    * G|g for GB

    :param value: the string to convert
    :param output_unit: result's unit (defaults to Bytes)
    :return: the corresponding integer value
    """
    m = re.match(r"(\d+)\s*([a-zA-Z]+)", value)
    if m is None:
        if re.match(r"\d+", value):
            return int(value)
        return 0
    if output_unit == "B":
        if m.group(2)[0] in ["K", "k"]:
            return int(m.group(1)) * 2 ** 10
        if m.group(2)[0] in ["M", "m"]:
            return int(m.group(1)) * 2 ** 20
        if m.group(2)[0] in ["G", "g"]:
            return int(m.group(1)) * 2 ** 30
    elif output_unit == "MB":
        if m.group(2)[0] in ["K", "k"]:
            return int(int(m.group(1)) / 2 ** 10)
        if m.group(2)[0] in ["M", "m"]:
            return int(m.group(1))
        if m.group(2)[0] in ["G", "g"]:
            return int(m.group(1)) * 2 ** 10
    else:
        raise ValueError("Unsupported output unit {}".format(output_unit))
    return 0


class NavigationParameters(object):
    """
    Just a simple object to manipulate navigation parameters.
    """

    def __init__(self, request, sessionkey):
        self.request = request
        self.sessionkey = sessionkey
        self.parameters = [("pattern", "", True),
                           ("criteria", "from_addr", False)]

    def __getitem__(self, key):
        """Retrieve an item."""
        if self.sessionkey not in self.request.session:
            raise KeyError
        return self.request.session[self.sessionkey][key]

    def __contains__(self, key):
        """Check if key is present."""
        if self.sessionkey not in self.request.session:
            return False
        return key in self.request.session[self.sessionkey]

    def __setitem__(self, key, value):
        """Set a new item."""
        self.request.session[self.sessionkey][key] = value

    def _store_page(self):
        """Specific method to store the current page."""
        self["page"] = int(self.request.GET.get("page", 1))

    def store(self):
        """Store navigation parameters into session.
        """
        if self.sessionkey not in self.request.session:
            self.request.session[self.sessionkey] = {}
        self._store_page()
        navparams = self.request.session[self.sessionkey]
        navparams["order"] = self.request.GET.get("sort_order", "-date")
        for param, defvalue, escape in self.parameters:
            value = self.request.GET.get(param, defvalue)
            if value is None:
                if param in navparams:
                    del navparams[param]
                continue
            navparams[param] = re.escape(value) if escape else value
        self.request.session.modified = True

    def get(self, param, default_value=None):
        """Retrieve a navigation parameter.

        Just a simple getter to avoid using the full key name to
        access a parameter.

        :param str param: parameter name
        :param defaultvalue: default value if none is found
        :return: parameter's value
        """
        if self.sessionkey not in self.request.session:
            return default_value
        return self.request.session[self.sessionkey].get(param, default_value)

    def remove(self, param):
        """Remove a navigation parameter from session.

        :param str param: parameter name
        """
        navparams = self.request.session[self.sessionkey]
        if param in navparams:
            del navparams[param]
