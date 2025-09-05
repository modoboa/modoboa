import os
import re
import socket
import struct
from email.utils import parseaddr

import idna

from django.conf import settings
from django.utils.translation import gettext as _

from rest_framework import authentication, exceptions

from modoboa.admin import models as admin_models
from modoboa.lib.email_utils import split_address, split_local_part, split_mailbox
from modoboa.lib.exceptions import InternalError
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools
from .models import Msgrcpt, Policy, Users
from .utils import smart_bytes, smart_str


class SelfServiceAuthentication(authentication.BaseAuthentication):

    def authenticate(self, request):
        from .sql_connector import SQLconnector

        mail_id = request._request.resolver_match.kwargs.get("pk")
        if request.method == "GET":
            rcpt = request.GET.get("rcpt")
            secret_id = request.GET.get("secret_id")
        else:
            rcpt = request.data.get("rcpt")
            secret_id = request.data.get("secret_id")
        if not mail_id or not rcpt or not secret_id:
            return None
        connector = SQLconnector()
        try:
            msgrcpt = connector.get_recipient_message(rcpt, mail_id)
        except Msgrcpt.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid credentials") from None
        if secret_id != smart_str(msgrcpt.mail.secret_id):
            raise exceptions.AuthenticationFailed("Invalid credentials")
        return (None, "selfservice")


class AMrelease:
    def __init__(self):
        conf = dict(param_tools.get_global_parameters("amavis"))
        try:
            if conf["am_pdp_mode"] == "inet":
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((conf["am_pdp_host"], conf["am_pdp_port"]))
            else:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.connect(conf["am_pdp_socket"])
        except OSError as err:
            raise InternalError(
                _("Connection to amavis failed: %s") % str(err)
            ) from None

    def decode(self, answer):
        def repl(match):
            return struct.pack("B", int(match.group(0)[1:], 16))

        return re.sub(rb"%([0-9a-fA-F]{2})", repl, answer)

    def __del__(self):
        self.sock.close()

    def sendreq(self, mailid, secretid, recipient, *others):
        self.sock.send(
            smart_bytes(
                f"""request=release
mail_id={smart_str(mailid)}
secret_id={smart_str(secretid)}
quar_type=Q
recipient={smart_str(recipient)}

"""
            )
        )
        answer = self.sock.recv(1024)
        answer = self.decode(answer)
        if re.search(rb"250 [\d\.]+ Ok", answer):
            return True
        return False


class SpamassassinClient:
    """A stupid spamassassin client."""

    def __init__(self, user, recipient_db):
        """Constructor."""
        conf = dict(param_tools.get_global_parameters("amavis"))
        self._sa_is_local = conf["sa_is_local"]
        self._default_username = conf["default_user"]
        self._recipient_db = recipient_db
        self._setup_cache = {}
        self._username_cache = []
        if user.role == "SimpleUsers":
            if conf["user_level_learning"]:
                self._username = user.email
        else:
            self._username = None
        self.error = None
        if self._sa_is_local:
            self._learn_cmd = self._find_binary("sa-learn")
            self._learn_cmd += " --{0} --no-sync -u {1}"
            self._learn_cmd_kwargs = {}
            self._expected_exit_codes = [0]
            self._sync_cmd = self._find_binary("sa-learn")
            self._sync_cmd += " -u {0} --sync"
        else:
            self._learn_cmd = self._find_binary("spamc")
            self._learn_cmd += " -d {} -p {}".format(
                conf["spamd_address"], conf["spamd_port"]
            )
            self._learn_cmd += " -L {0} -u {1}"
            self._learn_cmd_kwargs = {}
            self._expected_exit_codes = [5, 6]

    def _find_binary(self, name):
        """Find path to binary."""
        code, output = exec_cmd(f"which {name}")
        if not code:
            return smart_str(output).strip()
        known_paths = getattr(settings, "SA_LOOKUP_PATH", ("/usr/bin",))
        for path in known_paths:
            bpath = os.path.join(path, name)
            if os.path.isfile(bpath) and os.access(bpath, os.X_OK):
                return bpath
        raise InternalError(_("Failed to find {} binary").format(name))

    def _get_mailbox_from_rcpt(self, rcpt):
        """Retrieve a mailbox from a recipient address."""
        local_part, domname, extension = split_mailbox(rcpt, return_extension=True)
        try:
            mailbox = admin_models.Mailbox.objects.select_related("domain").get(
                address=local_part, domain__name=domname
            )
        except admin_models.Mailbox.DoesNotExist:
            alias = admin_models.Alias.objects.filter(
                address=f"{local_part}@{domname}",
                aliasrecipient__r_mailbox__isnull=False,
            ).first()
            if not alias:
                raise InternalError(_("No recipient found")) from None
            if alias.type != "alias":
                return None
            mailbox = alias.aliasrecipient_set.filter(r_mailbox__isnull=False).first()
        return mailbox

    def _get_domain_from_rcpt(self, rcpt):
        """Retrieve a domain from a recipient address."""
        local_part, domname = split_mailbox(rcpt)
        domain = admin_models.Domain.objects.filter(name=domname).first()
        if not domain:
            raise InternalError(_("Local domain not found"))
        return domain

    def _learn(self, rcpt, msg, mtype):
        """Internal method to call the learning command."""
        if self._username is None:
            if self._recipient_db == "global":
                username = self._default_username
            elif self._recipient_db == "domain":
                domain = self._get_domain_from_rcpt(rcpt)
                username = domain.name
                condition = (
                    username not in self._setup_cache
                    and setup_manual_learning_for_domain(domain)
                )
                if condition:
                    self._setup_cache[username] = True
            else:
                mbox = self._get_mailbox_from_rcpt(rcpt)
                if mbox is None:
                    username = self._default_username
                else:
                    if isinstance(mbox, admin_models.Mailbox):
                        username = mbox.full_address
                    elif isinstance(mbox, admin_models.AliasRecipient):
                        username = mbox.address
                    else:
                        username = None
                    condition = (
                        username is not None
                        and username not in self._setup_cache
                        and setup_manual_learning_for_mbox(mbox)
                    )
                    if condition:
                        self._setup_cache[username] = True
        else:
            username = self._username
            if username not in self._setup_cache:
                mbox = self._get_mailbox_from_rcpt(username)
                if mbox and setup_manual_learning_for_mbox(mbox):
                    self._setup_cache[username] = True
        if username not in self._username_cache:
            self._username_cache.append(username)
        cmd = self._learn_cmd.format(mtype, username)
        code, output = exec_cmd(cmd, pinput=smart_bytes(msg), **self._learn_cmd_kwargs)
        if code in self._expected_exit_codes:
            return True
        self.error = smart_str(output)
        return False

    def learn_spam(self, rcpt, msg):
        """Learn new spam."""
        return self._learn(rcpt, msg, "spam")

    def learn_ham(self, rcpt, msg):
        """Learn new ham."""
        return self._learn(rcpt, msg, "ham")

    def done(self):
        """Call this method at the end of the processing."""
        if self._sa_is_local:
            for username in self._username_cache:
                cmd = self._sync_cmd.format(username)
                exec_cmd(cmd, **self._learn_cmd_kwargs)


def create_user_and_policy(name, priority=7):
    """Create records.

    Create two records (a user and a policy) using :keyword:`name` as
    an identifier.

    :param str name: name
    :return: the new ``Policy`` object
    """
    policy, _ = Policy.objects.get_or_create(policy_name=name[:32])
    if not Users.objects.filter(email=name).exists():
        Users.objects.create(
            email=name, fullname=name, priority=priority, policy=policy
        )
    return policy


def create_user_and_use_policy(name, policy, priority=7):
    """Create a *users* record and use an existing policy.

    :param str name: user record name
    :param str policy: string or Policy instance
    """
    if isinstance(policy, str):
        policy = Policy.objects.get(policy_name=policy[:32])
    Users.objects.get_or_create(
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
    u.policy.save(update_fields=["policy_name"])
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
    conf = dict(param_tools.get_global_parameters("amavis"))
    if not conf["manual_learning"]:
        return False
    if user.role != "SuperAdmins":
        if user.has_perm("admin.view_domain"):
            manual_learning = (
                conf["domain_level_learning"] or conf["user_level_learning"]
            )
        else:
            manual_learning = conf["user_level_learning"]
        return manual_learning
    return True


def setup_manual_learning_for_domain(domain):
    """Setup manual learning if necessary.

    :return: True if learning has been setup, False otherwise
    """
    if Policy.objects.filter(sa_username=domain.name).exists():
        return False
    policy = Policy.objects.get(policy_name=f"@{domain.name[:32]}")
    policy.sa_username = domain.name
    policy.save()
    return True


def setup_manual_learning_for_mbox(mbox):
    """Setup manual learning if necessary.

    :return: True if learning has been setup, False otherwise
    """
    result = False
    if isinstance(mbox, admin_models.AliasRecipient) and mbox.r_mailbox is not None:
        mbox = mbox.r_mailbox
    if isinstance(mbox, admin_models.Mailbox):
        pname = mbox.full_address[:32]
        if not Policy.objects.filter(policy_name=pname).exists():
            policy = create_user_and_policy(pname)
            policy.sa_username = mbox.full_address
            policy.save()
            for alias in mbox.alias_addresses:
                create_user_and_use_policy(alias, policy)
            result = True
    return result


def make_query_args(address, exact_extension=True, wildcard=None, domain_search=False):
    assert isinstance(address, str), "address should be of type str"
    conf = dict(param_tools.get_global_parameters("amavis"))
    local_part, domain = split_address(address)
    if not conf["localpart_is_case_sensitive"]:
        local_part = local_part.lower()
    if domain:
        domain = domain.lstrip("@").rstrip(".")
        domain = domain.lower()
        orig_domain = domain
        domain = idna.encode(domain, uts46=True).decode("ascii")
    delimiter = conf["recipient_delimiter"]
    local_part, extension = split_local_part(local_part, delimiter=delimiter)
    query_args = []
    if conf["localpart_is_case_sensitive"] or (domain and domain != orig_domain):
        query_args.append(address)
    if extension:
        query_args.append(f"{local_part}{delimiter}{extension}@{domain}")
    if delimiter and not exact_extension and wildcard:
        query_args.append(f"{local_part}{delimiter}{wildcard}@{domain}")
    query_args.append(f"{local_part}@{domain}")
    if domain_search:
        query_args.append(f"@{domain}")
        query_args.append("@.")

    return query_args


def cleanup_email_address(address):
    address = parseaddr(address)
    if address[0]:
        return f"{address[0]} <{address[1]}>"
    return address[1]
