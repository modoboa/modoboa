# coding: utf-8
import socket
import re
import struct
import string
from functools import wraps
from django.core.urlresolvers import reverse
from django.db.models import Q
from modoboa.lib import parameters
from models import Msgrcpt

def selfservice(ssfunc=None):
    """Decorator used to expose views to the 'self-service' feature

    The 'self-service' feature allows users to act on quarantined
    messages without beeing authenticated.

    This decorator only acts as a 'router'.

    :param ssfunc: the function to call if the 'self-service'
                   pre-requisites are satisfied
    """
    def decorator(f):
        @wraps(f)
        def wrapped_f(request, *args, **kwargs):
            if request.user.is_authenticated():
                return f(request, *args, **kwargs)
            if parameters.get_admin("SELF_SERVICE") == "no":
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(reverse("modoboa.extensions.amavis.views.index"))
            return ssfunc(request, *args, **kwargs)
        return wrapped_f
    return decorator

class AMrelease(object):
    def __init__(self):
        mode = parameters.get_admin("AM_PDP_MODE")
        if mode == "inet":
            host = parameters.get_admin('AM_PDP_HOST')
            port = parameters.get_admin('AM_PDP_PORT')
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, int(port)))
        else:
            path = parameters.get_admin('AM_PDP_SOCKET')
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(path)

    def decode(self, answer):
        def repl(match):
            return struct.pack("B", string.atoi(match.group(0)[1:], 16))

        return re.sub(r"%([0-9a-fA-F]{2})", repl, answer)

    def __del__(self):
        self.sock.close()

    def sendreq(self, mailid, secretid, recipient, *others):
        self.sock.send("""request=release
mail_id=%s
secret_id=%s
quar_type=Q
recipient=%s

""" % (mailid, secretid, recipient))
        answer = self.sock.recv(1024)
        answer = self.decode(answer)
        if re.search("250 [\d\.]+ Ok", answer):
            return True
        return False
