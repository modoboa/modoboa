# -*- coding: utf-8 -*-
import os
import sys
import time
import hashlib, crypt, string
from random import Random
from django.http import HttpResponse
from django.conf import settings
from django import template
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils import simplejson
from modoboa.lib import parameters

def exec_cmd(cmd, **kwargs):
    import subprocess

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, **kwargs)
    output = p.communicate()[0]
    return p.returncode, output

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

def exec_as_vuser(cmd):
    code, output = exec_cmd("sudo -u %s %s" \
                                % (parameters.get_admin("VIRTUAL_UID", app="admin"), cmd))
    if code:
        exec_cmd("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True

def _ctx_ok(url):
    return {"status" : "ok", "url" : url}

def _ctx_ko(tpl, ctx):
    return {"status" : "ko", "content" : render_to_string(tpl, ctx)}

def static_url(path):
    """Returns the correct static url for a given file

    :param path: the targeted static media
    """
    if path.startswith("/"):
        path = path[1:]
    return "%s%s" % (settings.MEDIA_URL, path)

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

def decode(s, encodings=('utf8', 'latin1', 'windows-1252', 'ascii'), charset=None):
    if charset is not None:
        try:
            return s.decode(charset, 'ignore')
        except LookupError:
            pass

    for encoding in encodings:
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            pass
    return s.decode('ascii', 'ignore')

def is_not_localadmin(errortpl="error"):
    def dec(f):
        def wrapped_f(request, *args, **kwargs):
            if request.user.id == 1:
                return _render_error(request, errortpl, {
                        "error" : _("Invalid action, %(user)s is a local user" \
                                        % {"user" : request.user.username})
                        })
            return f(request, *args, **kwargs)

        wrapped_f.__name__ = f.__name__
        wrapped_f.__dict__ = f.__dict__
        wrapped_f.__doc__ = f.__doc__
        wrapped_f.__module__ = f.__module__
        return wrapped_f
    return dec

def db_table_exists(table, cursor=None):
    """Check if table exists

    Taken from here:
    https://gist.github.com/527113/307c2dec09ceeb647b8fa1d6d49591f3352cb034

    """
    try:
        if not cursor:
            from django.db import connection
            cursor = connection.cursor()
        if not cursor:
            raise Exception
        table_names = connection.introspection.get_table_list(cursor)
    except:
        raise Exception("unable to determine if the table '%s' exists" % table)
    else:
        return table in table_names

def _check_password(password, crypted):
    scheme = parameters.get_admin("PASSWORD_SCHEME", app="admin")
    if scheme == "crypt":
        return crypt.crypt(password, crypted) == crypted
    if scheme == "md5":
        return hashlib.md5(password).hexdigest() == crypted
    return password

def crypt_password(password):
    scheme = parameters.get_admin("PASSWORD_SCHEME", app="admin")
    if scheme == "crypt":
        salt = ''.join(Random().sample(string.letters + string.digits, 2))
        return crypt.crypt(password, salt)
    if scheme == "md5":
        return hashlib.md5(password).hexdigest()
    return password

