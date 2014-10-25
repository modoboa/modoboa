# coding: utf-8

from functools import wraps
import re
import socket
import string
import struct

from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from modoboa.lib import parameters
from modoboa.lib.exceptions import InternalError
from modoboa.lib.sysutils import exec_cmd
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
        if re.search(r"250 [\d\.]+ Ok", answer):
            return True
        return False


class SpamassassinClient(object):

    """A stupid spamassassin client."""

    def __init__(self, user):
        """Constructor."""
        self._sa_is_local = parameters.get_admin("SA_IS_LOCAL")
        if user.group == "SimpleUsers":
            user_manual_learning = parameters.get_admin("USER_MANUAL_LEARNING")
            if user_manual_learning == "yes":
                self._username = user.email
        else:
            self._username = parameters.get_admin("DEFAULT_USER")
        setup_manual_learning(user)
        self.error = None
        if self._sa_is_local == "yes":
            self._learn_cmd = "sa-learn --{0} --no-sync -u {1}"
            self._learn_cmd_kwargs = {}
            self._expected_exit_codes = [0]
        else:
            self._learn_cmd = "spamc -d {0} -p {1}".format(
                parameters.get_admin("SPAMD_ADDRESS"),
                parameters.get_admin("SPAMD_PORT")
            )
            self._learn_cmd += " -L {0} -u {1}"
            self._learn_cmd_kwargs = {}
            self._expected_exit_codes = [5, 6]

    def _learn(self, msg, mtype):
        """Internal method to call the learning command."""
        cmd = self._learn_cmd.format(mtype, self._username)
        code, output = exec_cmd(cmd, pinput=msg, **self._learn_cmd_kwargs)
        if code in self._expected_exit_codes:
            return True
        self.error = output
        return False

    def learn_spam(self, msg):
        """Learn new spam."""
        return self._learn(msg, "spam")

    def learn_ham(self, msg):
        """Learn new ham."""
        return self._learn(msg, "ham")

    def done(self):
        """Call this method at the end of the processing."""
        if self._sa_is_local:
            exec_cmd("sa-learn -u {0} --sync".format(self._username),
                     **self._learn_cmd_kwargs)


class QuarantineNavigationParameters(NavigationParameters):
    """
    Specific NavigationParameters subclass for the quarantine.
    """
    def __init__(self, request):
        super(QuarantineNavigationParameters, self).__init__(
            request, 'quarantine_navparams'
        )
        self.parameters += [
            ('msgtype', None, False), ('viewrequests', None, False)
        ]

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


def create_user_and_policy(name, priority=7):
    """Create records.

    Create two records (a user and a policy) using :keyword:`name` as
    an identifier.

    :param str name: name
    :return: the new ``Policy`` object
    """
    policy = Policy.objects.create(policy_name=name[:32])
    Users.objects.create(
        email=name, fullname=name, priority=priority, policy=policy
    )
    return policy


def create_user_and_use_policy(name, policy_name, priority=7):
    """Create a *users* record and use an existing policy.

    :param str name: user record name
    :param str policy_name: policy name
    """
    policy = Policy.objects.get(policy_name=policy_name[:32])
    Users.objects.create(
        email=name, fullname=name, priority=priority, policy=policy
    )


def update_user_and_policy(oldname, newname):
    """Update records.

    :param str oldname: old name
    :param str newname: new name
    """
    if oldname == newname:
        return
    u = Users.objects.get(email=oldname)
    u.email = newname
    u.fullname = newname
    u.policy.policy_name = newname[:32]
    u.policy.save()
    u.save()


def delete_user_and_policy(name):
    """Delete records.

    :param str name: identifier
    """
    try:
        u = Users.objects.get(email=name)
    except Users.DoesNotExist:
        return
    u.policy.delete()
    u.delete()


def delete_user(name):
    """Delete a *users* record.

    :param str name: user record name
    """
    try:
        Users.objects.get(email=name).delete()
    except Users.DoesNotExist:
        pass


def manual_learning_enabled(user):
    """Check if manual learning is enabled or not.

    Also check for :kw:`user` if necessary.

    :return: True if learning is enabled, False otherwise.
    """
    manual_learning = parameters.get_admin("MANUAL_LEARNING") == "yes"
    if manual_learning and user.group == "SimpleUsers":
        manual_learning = parameters.get_admin("USER_MANUAL_LEARNING") == "yes"
    return manual_learning


def setup_manual_learning(user):
    """Setup manual learning if necessary.

    :return: True if learning has been setup, False otherwise
    """
    result = False
    if user.group == "SimpleUsers":
        if not Policy.objects.exists(email=user.email):
            policy = create_user_and_policy(user.email)
            for alias in user.mailbox_set.all()[0].alias_addresses:
                create_user_and_use_policy(alias.full_address, policy)
            result = True
    return result
