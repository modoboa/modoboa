# coding: utf-8
import socket
import re
import struct
import string
from functools import wraps
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import parameters
from modoboa.lib.exceptions import InternalError
from modoboa.lib.webutils import NavigationParameters
from modoboa.extensions.amavis.models import Users, Policy



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
                return redirect_to_login(
                    reverse("modoboa.extensions.amavis.views.index")
                )
            return ssfunc(request, *args, **kwargs)
        return wrapped_f
    return decorator


class AMrelease(object):
    def __init__(self):
        mode = parameters.get_admin("AM_PDP_MODE")
        try:
            if mode == "inet":
                host = parameters.get_admin('AM_PDP_HOST')
                port = parameters.get_admin('AM_PDP_PORT')
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((host, int(port)))
            else:
                path = parameters.get_admin('AM_PDP_SOCKET')
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.connect(path)
        except socket.error, err:
            raise InternalError(
                _("Connection to amavis failed: %s" % str(err))
            )

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


class QuarantineNavigationParameters(NavigationParameters):
    """
    Specific NavigationParameters subclass for the quarantine.
    """
    def __init__(self, request):
        super(QuarantineNavigationParameters, self).__init__(
            request, 'quarantine_navparams'
        )
        self.parameters += [('msgtype', None, False)]

    def back_to_listing(self):
        """Return the current listing URL.

        Looks into the user's session and the current request to build
        the URL.

        :return: a string
        """
        url = "listing"
        params = []
        navparams = self.request.session[self.sessionkey]
        if "page" in navparams:
            params += ["page=%s" % navparams["page"]]
        if "order" in navparams:
            params += ["sort_order=%s" % navparams["order"]]
        params += ["%s=%s" % (p[0], navparams[p[0]])
                   for p in self.parameters if p[0] in navparams]
        if params:
            url += "?%s" % ("&".join(params))
        return url


def create_user_and_policy(name):
    """Create records.

    Create two records (a user and a policy) using :keyword:`name` as
    an identifier.

    :param str name: name
    """
    policy = Policy.objects.create(policy_name=name)
    Users.objects.create(
        email="@%s" % name, fullname=name,
        priority=7, policy=policy
    )


def create_user_and_use_policy(name, policy_name):
    """Create a *users* record and use an existing policy.

    :param str name: user record name
    :param str policy_name: policy name
    """
    policy = Policy.objects.get(policy_name=policy_name)
    Users.objects.create(
        email="@%s" % name, fullname=name,
        priority=7, policy=policy
    )


def update_user_and_policy(oldname, newname):
    """Update records.

    :param str oldname: old name
    :param str newname: new name
    """
    if oldname == newname:
        return
    u = Users.objects.get(email="@%s" % oldname)
    u.email = "@%s" % newname
    u.fullname = newname
    u.policy.policy_name = newname
    u.policy.save()
    u.save()


def delete_user_and_policy(name):
    """Delete records.

    :param str name: identifier
    """
    try:
        u = Users.objects.get(email="@%s" % name)
    except Users.DoesNotExist:
        return
    u.policy.delete()
    u.delete()


def delete_user(name):
    """Delete a *users* record.

    :param str name: user record name
    """
    try:
        Users.objects.get(email="@%s" % name).delete()
    except Users.DoesNotExist:
        pass
