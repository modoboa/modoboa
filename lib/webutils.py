# coding: utf-8

"""
This module contains extra functions/shortcuts used to render HTML.
"""
import sys
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django import template
from django.utils import simplejson
from django.conf import settings

def _render(request, tpl, user_context):
    """Custom rendering function

    Just a wrapper which automatically adds a RequestContext instance
    (useful to use settings variables like MEDIA_URL inside templates)
    """
    return render_to_response(tpl, user_context, 
                              context_instance=template.RequestContext(request))

def _render_to_string(request, tpl, user_context):
    """Custom rendering function

    Same as _render.
    """
    return render_to_string(tpl, user_context,
                            context_instance=template.RequestContext(request))

def _render_error(request, errortpl="error", user_context={}):
    return render_to_response("common/%s.html" % errortpl, user_context,
                              context_instance=template.RequestContext(request))

def render_actions(actions):
    t = template.Template("""
{% for a in actions %}
<a href="{{ a.url }}" name="{{ a.name }}" class="{{ a.class }}" rel="{{ a.rel }}"
   {% if a.confirm %}onclick="return confirm('{{ a.confirm }}')"{% endif %}>
  <img src="{{ a.img }}" border="0" title="{{ a.title }}" />
</a>
{% endfor %}
""")
    return t.render(template.Context({
                "actions" : actions
                }))

def _ctx_ok(url):
    return {"status" : "ok", "url" : url}

def _ctx_ko(tpl, ctx):
    return {"status" : "ko", "content" : render_to_string(tpl, ctx)}

def getctx(status, level=1, callback=None, **kwargs):
    if not callback:
        callername = sys._getframe(level).f_code.co_name
    else:
        callername = callback
    ctx = {"status" : status, "callback" : callername}
    for kw, v in kwargs.iteritems():
        ctx[kw] = v
    return ctx

def ajax_response(request, status="ok", respmsg=None,
                  url="", ajaxnav=False, norefresh=False, 
                  template=None, **kwargs):
    """Ajax response shortcut

    Simple shortcut that sends an JSON response. If a template is
    provided, a 'content' field will be added to the response,
    containing the result of this template rendering.

    :param request: a request object
    :param status: the response status ('ok' or 'ko)
    :param nexturl: url to display after receiving this response
    :param template: eventual template's path
    :param kwargs: dict used for template rendering
    """
    ctx = {}
    for k, v in kwargs.iteritems():
        ctx[k] = v
    if template is not None:
        content = _render_to_string(request, template, ctx)
    elif kwargs.has_key("content"):
        content = kwargs["content"]
    else:
        content = ""
    jsonctx = {"status" : status, "content" : content}
    if respmsg is not None:
        jsonctx["respmsg"] = respmsg
    if ajaxnav:
        jsonctx["ajaxnav"] = True
    if url != "":
        jsonctx["url"] = url
    jsonctx["norefresh"] = norefresh
    return HttpResponse(simplejson.dumps(jsonctx), mimetype="application/json")

def ajax_simple_response(content):
    """Simple AJAX response

    No extra formatting is done. The content is passed directly to simplejon.

    :param content: the response's content (list, dict, string)
    """
    return HttpResponse(simplejson.dumps(content), mimetype="application/json")

def static_url(path):
    """Returns the correct static url for a given file

    :param path: the targeted static media
    """
    if path.startswith("/"):
        path = path[1:]
    return "%s%s" % (settings.MEDIA_URL, path)
