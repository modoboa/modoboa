# -*- coding: utf-8 -*-
import os
import sys
import time
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from mailng.lib import parameters

def exec_cmd(cmd):
    import subprocess

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = p.communicate()[0]
    return p.returncode, output

def _render(request, tpl, user_context):
    return render_to_response(tpl, user_context, 
                              context_instance=RequestContext(request))

def _render_error(request, errortpl="error", user_context={}):
    return render_to_response("common/%s.html" % errortpl, user_context,
                              context_instance=RequestContext(request))

def exec_as_vuser(cmd):
    code, output = exec_cmd("sudo -u %s %s" \
                                % (parameters.get("admin", "VIRTUAL_UID"), cmd))
    if code:
        exec_cmd("echo '%s' >> /tmp/vmail.log" % output)
        return False
    return True

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

def decode(s, encodings=('utf8', 'latin1', 'windows-1252', 'ascii')):
    for encoding in encodings:
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            pass
    return s.decode('ascii', 'ignore')

def is_not_localadmin(errortpl="error"):
    def dec(f):
        def wrapped_f(request, **kwargs):
            if request.user.id == 1:
                return _render_error(request, errortpl, {
                        "error" : _("Invalid action, %s is a local user" \
                                        % request.user.username)
                        })
            return f(request, **kwargs)
        return wrapped_f
    return dec

class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance

