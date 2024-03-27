# coding: utf-8
"""
:mod:`imaputils` --- Extra IMAPv4 utilities
-------------------------------------------
"""

import imaplib
import re
from operator import itemgetter
import socket
import ssl

import six

from django.utils.encoding import smart_bytes
from django.utils.translation import gettext as _

from modoboa.lib import imap_utf7  # NOQA
from modoboa.lib.connections import ConnectionsManager
from modoboa.lib.exceptions import ModoboaException, InternalError
from modoboa.parameters import tools as param_tools


class ImapError(ModoboaException):

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return str(self.reason)


@six.add_metaclass(ConnectionsManager)
class IMAPconnector(object):
    """The IMAPv4 connector."""

    list_base_pattern = r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" "?(?P<name>[^"]*)"?'
    list_response_pattern_literal = re.compile(
        r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" \{(?P<namelen>\d+)\}'
    )
    list_response_pattern = re.compile(list_base_pattern)
    listextended_response_pattern = re.compile(
        list_base_pattern + r"\s*(?P<childinfo>.*)"
    )

    def __init__(self, user=None, password=None):
        self.__hdelimiter = None
        self.conf = dict(param_tools.get_global_parameters("sievefilters"))
        self.address = self.conf["imap_server"]
        self.port = self.conf["imap_port"]
        self.login(user, password)

    def _cmd(self, name, *args, **kwargs):
        """IMAP command wrapper

        To simplify errors handling, this wrapper calls the
        appropriate method (``uid`` or FIXME) and then check the
        return code. If an error has occured, an ``ImapError``
        exception is raised.

        For specific commands commands (FETCH, ...), the result is
        parsed using the IMAPclient module before being returned.

        :param name: the command's name
        :return: the command's result
        """
        try:
            typ, data = self.m._simple_command(name, *args)
        except imaplib.IMAP4.error as e:
            raise ImapError(e)
        if typ == "NO":
            raise ImapError(data)
        if "responses" not in kwargs:
            if name not in self.m.untagged_responses:
                return None
            return self.m.untagged_responses.pop(name)
        res = []
        for r in kwargs["responses"]:
            if r not in self.m.untagged_responses:
                return None
            res.append(self.m.untagged_responses.pop(r))
        return res

    @property
    def hdelimiter(self):
        """Return the default hierachy delimiter.

        This is a simple way to retrieve the default delimiter (see
        http://www.imapwiki.org/ClientImplementation/MailboxList).

        :return: a string
        """
        if self.__hdelimiter is None:
            data = self._cmd("LIST", '""', '""')
            m = self.list_response_pattern.match(data[0].decode())
            if m is None:
                raise InternalError(_("Failed to retrieve hierarchy delimiter"))
            self.__hdelimiter = m.group("delimiter")
        return self.__hdelimiter

    def refresh(self, user, password):
        """Check if current connection needs a refresh

        Is it really secure?
        """
        if self.m is not None:
            try:
                self._cmd("NOOP")
            except ImapError:
                if hasattr(self, "current_mailbox"):
                    del self.current_mailbox
            else:
                return

        self.login(user, password)

    def login(self, user, passwd):
        """Custom login method

        We connect to the server, issue a LOGIN command. If
        successfull, we try to record a eventuel CAPABILITY untagged
        response. Otherwise, we issue the command.

        :param user: username
        :param passwd: password
        """
        try:
            if self.conf["imap_secured"]:
                self.m = imaplib.IMAP4_SSL(self.address, self.port)
            else:
                self.m = imaplib.IMAP4(self.address, self.port)
        except (socket.error, imaplib.IMAP4.error, ssl.SSLError) as error:
            raise ImapError(_("Connection to IMAP server failed: %s" % error))

        passwd = self.m._quote(passwd)
        data = self._cmd("LOGIN", smart_bytes(user), smart_bytes(passwd))
        self.m.state = "AUTH"
        if "CAPABILITY" in self.m.untagged_responses:
            self.capabilities = (
                self.m.untagged_responses.pop("CAPABILITY")[0].decode().split()
            )
        else:
            data = self._cmd("CAPABILITY")
            self.capabilities = data[0].decode().split()

    def logout(self):
        """Logout from server."""
        try:
            self._cmd("CHECK")
        except ImapError:
            pass
        self._cmd("LOGOUT")
        del self.m
        self.m = None
        if hasattr(self, "current_mailbox"):
            del self.current_mailbox

    def _listmboxes(self, topmailbox, mailboxes):
        """Retrieve mailboxes list."""
        pattern = (
            '"{0}{1}%"'.format(
                topmailbox.encode("imap4-utf-7").decode(), self.hdelimiter
            )
            if topmailbox
            else "%"
        )
        resp = self._cmd("LIST", '""', pattern, "RETURN", "(CHILDREN)")
        newmboxes = []
        for mb in resp:
            if not mb:
                continue
            if type(mb) in [list, tuple]:
                flags, delimiter, namelen = self.list_response_pattern_literal.match(
                    mb[0].decode()
                ).groups()
                name = mb[1][0 : int(namelen)]
            else:
                flags, delimiter, name, childinfo = (
                    self.listextended_response_pattern.match(mb.decode()).groups()
                )
            flags = flags.split(" ")
            name = bytearray(name, "utf-8")
            name = name.decode("imap4-utf-7")
            mdm_found = False
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    mdm_found = True
                    descr = mailboxes[idx]
                    break
            if not mdm_found:
                descr = {"name": name}
                newmboxes += [descr]

            if "\\Marked" in flags or "\\UnMarked" not in flags:
                descr["send_status"] = True
            if "\\HasChildren" in flags:
                if "\\NonExistent" in flags:
                    descr["removed"] = True
                descr["path"] = name
                descr["sub"] = []

        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    def getmboxes(self, user, topmailbox=""):
        """Returns a list of mailboxes for a particular user

        By default, only the first level of mailboxes under
        ``topmailbox`` is returned.

        :param user: a ``User`` instance
        :param topmailbox: the mailbox where to start in the tree
        :return: a list
        """
        if topmailbox:
            md_mailboxes = []
        else:
            md_mailboxes = [
                {"name": "INBOX", "class": "fa fa-inbox"},
                {
                    "name": user.parameters.get_value("drafts_folder"),
                    "class": "fa fa-file",
                },
                {"name": "Junk", "class": "fa fa-fire"},
                {
                    "name": user.parameters.get_value("sent_folder"),
                    "class": "fa fa-envelope",
                },
                {
                    "name": user.parameters.get_value("trash_folder"),
                    "class": "fa fa-trash",
                },
            ]
        self._listmboxes(topmailbox, md_mailboxes)

        return md_mailboxes


def get_imapconnector(request):
    """Simple shortcut to create a connector

    :param request: a ``Request`` object
    """
    imapc = IMAPconnector(
        user=request.user.username, password=request.session["password"]
    )
    return imapc
