# coding: utf-8
"""
:mod:`imaputils` --- Extra IMAPv4 utilities
-------------------------------------------
"""
import imaplib
import re
import ssl
from functools import wraps

from django.utils.translation import ugettext as _

from modoboa.lib import parameters, imap_utf7  # NOQA
from modoboa.lib.connections import ConnectionsManager
from modoboa.lib.exceptions import InternalError

from .exceptions import ImapError
from .fetch_parser import parse_fetch_response

# imaplib.Debug = 4


class capability(object):

    """
    Simple decorator to check if the server presents the required
    capability. If not, a fallback method is called instead.

    :param name: the capability name (upper case)
    :param fallback_method: a method's name
    """

    def __init__(self, name, fallback_method):
        self.name = name
        self.fallback_method = fallback_method

    def __call__(self, method):
        @wraps(method)
        def wrapped_func(cls, *args, **kwargs):
            if self.name in cls.capabilities:
                return method(cls, *args, **kwargs)
            return getattr(cls, self.fallback_method)(cls, **kwargs)

        return wrapped_func


class IMAPconnector(object):

    """The IMAPv4 connector."""

    __metaclass__ = ConnectionsManager

    list_base_pattern = (
        r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" "?(?P<name>[^"]*)"?'
    )
    list_response_pattern_literal = re.compile(
        r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" \{(?P<namelen>\d+)\}')
    list_response_pattern = re.compile(list_base_pattern)
    listextended_response_pattern = \
        re.compile(list_base_pattern + r'\s*(?P<childinfo>.*)')

    def __init__(self, user=None, password=None):
        self.__hdelimiter = None
        self.address = parameters.get_admin("IMAP_SERVER", "core")
        self.port = int(parameters.get_admin("IMAP_PORT", "core"))
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
        if name in ['FETCH', 'SORT', 'STORE', 'COPY', 'SEARCH']:
            try:
                typ, data = self.m.uid(name, *args)
            except imaplib.IMAP4.error as e:
                raise ImapError(e)
            if typ == "NO":
                raise ImapError(data)
            if name == 'FETCH':
                return parse_fetch_response(data)
            return data

        try:
            typ, data = self.m._simple_command(name, *args)
        except imaplib.IMAP4.error as e:
            raise ImapError(e)
        if typ == "NO":
            raise ImapError(data)
        if 'responses' not in kwargs:
            if name not in self.m.untagged_responses:
                return None
            return self.m.untagged_responses.pop(name)
        res = []
        for r in kwargs['responses']:
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
            data = self._cmd("LIST", "", "")
            m = self.list_response_pattern.match(data[0])
            if m is None:
                raise InternalError(_("Failed to retrieve hierarchy delimiter"))
            self.__hdelimiter = m.group('delimiter')
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
        import socket

        if isinstance(user, unicode):
            user = user.encode("utf-8")
        if isinstance(passwd, unicode):
            passwd = passwd.encode("utf-8")
        try:
            secured = parameters.get_admin("IMAP_SECURED", "core")
            if secured == "yes":
                self.m = imaplib.IMAP4_SSL(self.address, self.port)
            else:
                self.m = imaplib.IMAP4(self.address, self.port)
        except (socket.error, imaplib.IMAP4.error, ssl.SSLError) as error:
            raise ImapError(_("Connection to IMAP server failed: %s" % error))

        data = self._cmd("LOGIN", user, passwd)
        self.m.state = "AUTH"
        if "CAPABILITY" in self.m.untagged_responses:
            self.capabilities = \
                self.m.untagged_responses.pop('CAPABILITY')[0].split()
        else:
            data = self._cmd("CAPABILITY")
            self.capabilities = data[0].split()

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

    def _listmboxes_simple(self, topmailbox='INBOX', mailboxes=None, **kwargs):
        # data = self._cmd("LIST", "", "*")
        if not mailboxes:
            mailboxes = []
        (status, data) = self.m.list()
        newmboxes = []
        for mb in data:
            flags, delimiter, name = self.list_response_pattern.match(
                mb).groups()
            name = name.strip('"').decode("imap4-utf-7")
            mdm_found = False
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    mdm_found = True
                    descr = mailboxes[idx]
                    break
            if not mdm_found:
                descr = dict(name=name)
                newmboxes += [descr]

            if re.search("\%s" % delimiter, name):
                parts = name.split(delimiter)
                if "path" not in descr:
                    descr["path"] = parts[0]
                    descr["sub"] = []
                if self._parse_mailbox_name(descr["sub"], parts[0], delimiter,
                                            parts[1:]):
                    descr["class"] = "subfolders"
                continue

        from operator import itemgetter
        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    @capability('LIST-EXTENDED', '_listmboxes_simple')
    def _listmboxes(self, topmailbox, mailboxes):
        """Retrieve mailboxes list."""
        pattern = (
            "{0}{1}%".format(topmailbox.encode("imap4-utf-7"), self.hdelimiter)
            if topmailbox else "%"
        )
        resp = self._cmd("LIST", "", pattern, "RETURN", "(CHILDREN)")
        newmboxes = []
        for mb in resp:
            if not mb:
                continue
            if type(mb) in [str, unicode]:
                flags, delimiter, name, childinfo = \
                    self.listextended_response_pattern.match(mb).groups()
            else:
                flags, delimiter, namelen = (
                    self.list_response_pattern_literal.match(mb[0]).groups()
                )
                name = mb[1][0:int(namelen)]
            flags = flags.split(' ')
            name = name.decode("imap4-utf-7")
            mdm_found = False
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    mdm_found = True
                    descr = mailboxes[idx]
                    break
            if not mdm_found:
                descr = dict(name=name)
                newmboxes += [descr]

            if r'\Marked' in flags or r'\UnMarked' not in flags:
                descr["send_status"] = True
            if r'\HasChildren' in flags:
                if r'\NonExistent' in flags:
                    descr["removed"] = True
                descr["path"] = name
                descr["sub"] = []

        from operator import itemgetter
        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    def getmboxes(
            self, user, topmailbox=''):
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
                {"name": parameters.get_user(user, "DRAFTS_FOLDER"),
                 "class": "fa fa-file"},
                {"name": 'Junk', "class": "fa fa-fire"},
                {"name": parameters.get_user(user, "SENT_FOLDER"),
                 "class": "fa fa-envelope"},
                {"name": parameters.get_user(user, "TRASH_FOLDER"),
                 "class": "fa fa-trash"}
            ]
        self._listmboxes(topmailbox, md_mailboxes)

        return md_mailboxes


def get_imapconnector(request):
    """Simple shortcut to create a connector

    :param request: a ``Request`` object
    """
    imapc = IMAPconnector(user=request.user.username,
                          password=request.session["password"])
    return imapc


if __name__ == "__main__":
    import doctest
    doctest.testmod()
