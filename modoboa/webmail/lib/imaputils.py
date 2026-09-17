"""Extra IMAPv4 utilities."""

import email
import imaplib
import logging
import re
import ssl
import time

from django.conf import settings
from django.utils.translation import gettext as _

from modoboa.lib import imap_utf7  # noqa
from modoboa.lib import oauth2
from modoboa.lib.exceptions import InternalError
from modoboa.parameters import tools as param_tools
from modoboa.webmail import constants

from ..exceptions import (
    ImapError,
    InvalidImapArgument,
    MailboxOperationError,
    WebmailInternalError,
)
from . import imapheader
from .fetch_parser import FetchResponseParser

logger = logging.getLogger("modoboa.webmail")

# imaplib.Debug = 4

# workaround for the "got more than 10000 bytes" exception. MAXLINE
# value set to 1M, as on latest python versions.
MAXLINE = 1000000
if hasattr(imaplib, "_MAXLINE") and imaplib._MAXLINE < MAXLINE:
    imaplib._MAXLINE = MAXLINE

# Keep a reference to the real exception class: tests replace
# imaplib.IMAP4 with a mock, which would also replace IMAP4.error.
IMAP4Error = imaplib.IMAP4.error

# A message UID set: one or more positive integers separated by commas.
UID_RE = re.compile(r"^[0-9]+(?:,[0-9]+)*$")
# A MIME part number: dot-separated positive integers (e.g. "1", "2.1").
PARTNUM_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")

# A THREAD response only contains UIDs, parenthesis and spaces.
THREAD_RESPONSE_RE = re.compile(r"^[0-9() ]*$")
THREAD_TOKEN_RE = re.compile(r"[()]|[0-9]+")


def validate_imap_uid(value):
    """Ensure a message UID (set) is safe to pass to imaplib.

    Prevents IMAP command injection (CWE-93/CWE-74): imaplib does not
    reject CRLF or quote command arguments, so any user-controlled value
    reaching a command must be strictly validated first.
    """
    if value is None or not UID_RE.match(str(value)):
        raise InvalidImapArgument(_("Invalid message identifier"))
    return str(value)


def validate_imap_partnum(value):
    """Ensure a MIME part number is safe to pass to imaplib."""
    if value is None or not PARTNUM_RE.match(str(value)):
        raise InvalidImapArgument(_("Invalid part number"))
    return str(value)


def escape_search_pattern(pattern: str) -> str:
    """Escape a user pattern before placing it in an IMAP quoted string.

    Control characters (including CR/LF) cannot appear in an IMAP
    quoted string and would allow command injection, so they are
    rejected. Backslashes and double quotes are backslash-escaped as
    required by RFC 3501.
    """
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in pattern):
        raise InvalidImapArgument(_("Invalid search pattern"))
    return pattern.replace("\\", "\\\\").replace('"', '\\"')


def quote_mailbox_name(name: str) -> bytes:
    """Encode a mailbox name to imap4-utf-7 and return it as a quoted string.

    Double quotes and backslashes are left untouched by the imap4-utf-7
    codec, so they must be backslash-escaped, otherwise a crafted name
    could break out of the quoted string and inject extra command
    arguments. Control characters are rejected.
    """
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in name):
        raise InvalidImapArgument(_("Invalid mailbox name"))
    encoded = name.encode("imap4-utf-7")
    return b'"' + encoded.replace(b"\\", b"\\\\").replace(b'"', b'\\"') + b'"'


def parse_thread_response(data: list | None) -> list[list[str]]:
    """Turn a THREAD response into a flat list of threads.

    The server answers with nested groups (RFC 5256), for instance
    ``(2)(3 6 (4 23)(44 7 96))``: every UID of a top level group belongs
    to the same conversation, whatever its depth. Only that grouping is
    kept here, in the order given by the server, which is the order of
    the conversation itself.

    An unexpected reply (unbalanced parenthesis, unknown token) is
    logged and ignored rather than raising: a broken thread listing must
    not break the mailbox.
    """
    if not data:
        return []
    raw = b" ".join(part for part in data if part).decode("ascii", "replace").strip()
    if raw.upper().startswith("THREAD"):
        raw = raw[len("THREAD") :]
    if not THREAD_RESPONSE_RE.match(raw):
        logger.warning("Unexpected THREAD response: %s", raw[:200])
        return []
    threads: list[list[str]] = []
    current: list[str] | None = None
    depth = 0
    for token in THREAD_TOKEN_RE.findall(raw):
        if token == "(":
            depth += 1
            if depth == 1:
                current = []
        elif token == ")":
            depth -= 1
            if depth < 0:
                logger.warning("Unbalanced THREAD response: %s", raw[:200])
                return []
            if depth == 0 and current:
                threads.append(current)
                current = None
        elif current is not None:
            current.append(token)
        else:
            # A bare UID outside of any group is a thread of its own
            threads.append([token])
    if depth:
        logger.warning("Unbalanced THREAD response: %s", raw[:200])
        return []
    return threads


class BodyStructure:
    """
    BODYSTRUCTURE response parser.

    Just a simple class that tries to distinguish content parts from
    attachments.
    """

    current_mailbox: str

    def __init__(self, definition: list | None = None) -> None:
        self.is_multipart = False
        self.contents: dict[str, list] = {}
        self.attachments: list[dict] = []
        self.inlines: dict[str, dict] = {}

        if definition is not None:
            self.load_from_definition(definition)

    def __store_part(self, definition: list, pnum: str, multisubtype: str) -> None:
        """Store the given message part in the appropriate category.

        This method sort parts in two categories:

        * contents (what is going to be displayed)
        * attachments

        As there is no official definition about what is a content and
        what is an attachment, the following rules are applied:

        * If the MIME type is text/plain or text/html:

         * If no previous part of this type has already been seen,
           it's a content
         * Otherwise it's an attachment

        * Else, if the multipart subtype is related, we consider this
          part as content because it is certainly an embedded image

        * Any other MIME type is considered as an attachment (for now)

        :param definition: a part definition (list)
        :param pnum: the part's number
        :param multisubtype: the multipart subtype

        """
        pnum = "1" if pnum is None else pnum
        params = {
            "pnum": pnum,
            "params": definition[2],
            "cid": definition[3],
            "description": definition[4],
            "encoding": definition[5],
            "size": definition[6],
        }
        mtype = definition[0].lower()
        subtype = definition[1].lower()
        ftype = f"{definition[0].lower()}/{subtype}"
        if ftype in ("text/plain", "text/html"):
            if subtype not in self.contents:
                self.contents[subtype] = [params]
            else:
                self.contents[subtype].append(params)
            return
        elif multisubtype in ["related"]:
            params["Content-Type"] = ftype
            self.inlines[params["cid"].strip("<>")] = params
            return

        params["Content-Type"] = ftype
        if len(definition) > 7:
            extensions = ["md5", "disposition", "language", "location"]
            if mtype == "text":
                extensions = ["textlines"] + extensions
            elif ftype == "message/rfc822":
                extensions = ["envelopestruct", "bodystruct", "textlines"] + extensions
            for idx, value in enumerate(definition[7:]):
                params[extensions[idx]] = value

        self.attachments += [params]

    def load_from_definition(
        self, definition: list, multisubtype: str | None = None
    ) -> None:
        for mp in definition:
            if isinstance(mp, list):
                if isinstance(mp[0], list):
                    self.load_from_definition(mp, mp[1])
                else:
                    self.load_from_definition(mp)
            elif isinstance(mp, dict):
                if isinstance(mp["struct"][0], list):
                    self.load_from_definition(mp["struct"][0], mp["struct"][1])
                    continue
                self.__store_part(mp["struct"], mp["partnum"], multisubtype)

    def has_attachments(self) -> int:
        return len(self.attachments)

    def find_attachment(self, pnum: str) -> dict | None:
        for att in self.attachments:
            if pnum == att["pnum"]:
                return att
        return None


# Search criteria understood by parse_search_parameters, mapped to their
# IMAP key
SEARCH_KEYS = {
    "from_addr": "FROM",
    "to": "TO",
    "cc": "CC",
    "subject": "SUBJECT",
    "body": "BODY",
}

SEARCH_CRITERION_ALIASES = {
    # Kept for compatibility
    "both": "from_addr,subject",
    # What the single search field of the interface looks for
    "all": "from_addr,to,cc,subject,body",
}


class IMAPconnector:
    """The IMAPv4 connector."""

    namespaces_pattern = re.compile(r"(\(\(.+?\)\)|NIL)")
    namespace_pattern = re.compile(r'\("(?P<prefix>.*?)" "(?P<delimiter>.+?)"\)')
    list_base_pattern = r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" "?(?P<name>[^"]*)"?'
    list_response_pattern_literal = re.compile(
        r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" \{(?P<namelen>\d+)\}'
    )
    list_response_pattern = re.compile(list_base_pattern)
    listextended_response_pattern = re.compile(
        list_base_pattern + r"\s*(?P<childinfo>.*)"
    )
    unseen_pattern = re.compile(r"[^\(]+\(UNSEEN (\d+)\)")
    # STATUS response sent along a LIST reply: '"Archive" (MESSAGES 3 UNSEEN 1)'
    status_response_pattern = re.compile(
        r'^(?:STATUS\s+)?"?(?P<name>[^"(]*?)"?\s*\((?P<items>[^)]*)\)\s*$'
    )
    status_unseen_pattern = re.compile(r"UNSEEN (\d+)")

    def __init__(self, user: str, password: str, with_namespaces: bool = True) -> None:
        self.__hdelimiter: str | None = None
        self.__ns_prefixes: dict = {}
        self.quota_usage: int = -1
        self.quota_limit: int | None = None
        self.quota_current: int | None = None
        self.criterions: list = []
        self.conf = dict(param_tools.get_global_parameters("webmail"))
        self.address = self.conf["imap_server"]
        self.port = self.conf["imap_port"]
        self.user = user
        self.password = password
        self.with_namespaces = with_namespaces
        # Unseen counters collected from the last LIST reply
        self._unseen_counters: dict[str, int] = {}
        # Number of opened "with" blocks using this connector
        self._usage_count = 0
        # True when the connection lifetime is tied to a request
        self.managed = False

    def __enter__(self):
        """Open the connection, or join the one already opened.

        Blocks can be nested (a viewset using a connector while building
        an ImapEmail, for example): only the outermost one authenticates.
        """
        self._usage_count += 1
        # A request-scoped connector stays open between blocks: only
        # authenticate when there is no connection yet.
        if self._usage_count == 1 and not self.connected:
            self.login(self.user, self.password)
            if self.with_namespaces:
                self.load_namespaces()
        return self

    def __exit__(self, *args):
        self._usage_count = max(self._usage_count - 1, 0)
        # A request-scoped connector is closed once the request is over
        if self._usage_count == 0 and not self.managed:
            self.logout()

    @property
    def connected(self) -> bool:
        return getattr(self, "m", None) is not None

    def _cmd(self, name: str, *args, **kwargs) -> list | None:
        """IMAP command wrapper.

        To simplify errors handling, this wrapper calls the
        appropriate method (``uid`` or FIXME) and then check the
        return code. If an error has occured, an ``ImapError``
        exception is raised.

        For specific commands commands (FETCH, ...), the result is
        parsed using the IMAPclient module before being returned.

        :param name: the command's name
        :return: the command's result
        """
        if name in ["FETCH", "SORT", "STORE", "COPY", "SEARCH", "MOVE", "THREAD"]:
            try:
                typ, data = self.m.uid(name, *args)
            except IMAP4Error as e:
                raise ImapError(e) from None
            if typ == "NO":
                raise ImapError(data)
            if name == "FETCH":
                return FetchResponseParser().parse(data)
            return data

        try:
            typ, data = self.m._simple_command(name, *args)
        except IMAP4Error as e:
            raise ImapError(e) from None
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

        :return: a string
        """
        if self.__hdelimiter is None:
            raise InternalError(_("Failed to retrieve hierarchy delimiter"))
        return self.__hdelimiter

    def login(self, user: str, rawtoken: str) -> None:
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
        except (OSError, IMAP4Error, ssl.SSLError) as error:
            raise ImapError(_(f"Connection to IMAP server failed: {error}")) from None

        dev_mode = getattr(settings, "WEBMAIL_DEV_MODE", False)
        if not dev_mode:
            token = oauth2.build_oauthbearer_string(user, rawtoken)
            data = self._cmd("AUTHENTICATE", b"OAUTHBEARER", token)
        else:
            user = bytes(settings.WEBMAIL_DEV_USERNAME, "utf-8")
            passwd = self.m._quote(settings.WEBMAIL_DEV_PASSWORD)
            # Starting with Python 3.13, _quote() returns bytes
            if not isinstance(passwd, bytes):
                passwd = bytes(passwd, "utf-8")
            data = self._cmd("LOGIN", user, passwd)
        self.m.state = "AUTH"
        if "CAPABILITY" in self.m.untagged_responses:
            self.capabilities = (
                self.m.untagged_responses.pop("CAPABILITY")[0].decode().split()
            )
        else:
            data = self._cmd("CAPABILITY")
            self.capabilities = data[0].decode().split()

    def logout(self) -> None:
        """Logout from server.

        The connection may already be gone (server timeout or restart):
        the commands below then fail for no useful reason, since the
        connection is dropped anyway. The socket is always closed, even
        when the server never answered our LOGOUT.
        """
        if not self.connected:
            return
        self._usage_count = 0
        try:
            self._cmd("CHECK")
            self._cmd("LOGOUT")
        except (ImapError, OSError):
            pass
        finally:
            try:
                self.m.shutdown()
            except (IMAP4Error, OSError):
                pass
            self.m = None
            if hasattr(self, "current_mailbox"):
                del self.current_mailbox

    def load_namespaces(self) -> None:
        """Load available namespaces."""
        data = self._cmd("NAMESPACE")
        nslist = self.namespaces_pattern.findall(data[0].decode())
        for pos, item in enumerate(["personal", "others", "public"]):
            if nslist[pos] == "NIL":
                continue
            ns = nslist[pos][1:-1]
            for m in self.namespace_pattern.finditer(ns):
                if self.__hdelimiter is None:
                    self.__hdelimiter = m.group("delimiter")
                if item not in self.__ns_prefixes:
                    self.__ns_prefixes[item] = []
                self.__ns_prefixes[item].append(m.group("prefix"))

    def parse_search_parameters(self, criterion: str, pattern: str) -> None:
        """Parse search information and apply them."""

        def or_criterion(old, c):
            if old == "":
                return c
            return f"OR {old} {c}"

        criterion = SEARCH_CRITERION_ALIASES.get(criterion, criterion)

        if not pattern:
            criterions = "ALL"
        else:
            pattern = escape_search_pattern(pattern)
            criterions = ""
            for c in criterion.split(","):
                key = SEARCH_KEYS.get(c.strip())
                if key is None:
                    continue
                criterions = or_criterion(criterions, f'({key} "{pattern}")')
            if criterions == "":
                # None of the given criteria is known: search everywhere
                # rather than sending an empty, invalid command.
                criterions = f'(TEXT "{pattern}")'

        self.criterions = [bytearray(criterions, "utf8")]

    @property
    def has_sort(self) -> bool:
        """Does the server support the SORT extension (RFC 5256)?"""
        return "SORT" in getattr(self, "capabilities", [])

    @property
    def has_thread(self) -> bool:
        """Does the server support the THREAD extension (RFC 5256)?"""
        return "THREAD=REFERENCES" in getattr(self, "capabilities", [])

    def messages_count(self, **kwargs) -> int:
        """An enhanced version of messages_count.

        With IMAP, to know how many messages a mailbox contains, we
        have to make a request to the server. To avoid requests
        multiplications, we sort messages in the same time. This will
        be usefull for other methods.

        :param order: sorting order
        :param folder: mailbox to scan
        """
        if "order" in kwargs and kwargs["order"]:
            sign = kwargs["order"][:1]
            criterion = kwargs["order"][1:].upper()
            if sign == "-":
                criterion = f"REVERSE {criterion}"
        else:
            criterion = "REVERSE DATE"
        mbox = kwargs.get("mbox")

        # FIXME: pourquoi suis je obligé de faire un SELECT ici?  un
        # EXAMINE plante mais je pense que c'est du à une mauvaise
        # lecture des réponses de ma part...
        self.select_mailbox(mbox, readonly=False)
        if self.has_sort:
            data = self._cmd(
                "SORT",
                f"({criterion})",
                b"UTF-8",
                b"(NOT DELETED)",
                *self.criterions,
            )
            self.messages = data[0].decode().split()
        else:
            self.messages = self._search_messages(
                reverse=criterion.startswith("REVERSE")
            )
        self.getquota(mbox)
        return len(self.messages)

    def _search_messages(self, reverse: bool = True) -> list:
        """List the messages of the selected mailbox without SORT.

        SORT is an extension: servers that lack it only answer SEARCH,
        which returns UIDs in ascending order. Messages are then ordered
        by arrival instead of by their Date header, which is the closest
        approximation we can give without fetching every date.
        """
        data = self._cmd(
            "SEARCH",
            b"CHARSET",
            b"UTF-8",
            b"(NOT DELETED)",
            *self.criterions,
        )
        messages = data[0].decode().split()
        messages.sort(key=int, reverse=reverse)
        return messages

    def threads_count(self, **kwargs) -> int:
        """Group the messages of a mailbox into conversations.

        ``messages_count`` is called first: it selects the mailbox and
        gives the order of the messages, with SORT when the server
        offers it and by arrival otherwise. That order then ranks the
        threads, so that a conversation which receives a new message
        comes back to the top of the listing.

        The result is stored in ``self.threads``, as a list of UID
        lists. Inside a thread, UIDs keep the order given by the server,
        which is the order of the conversation.
        """
        self.messages_count(**kwargs)
        rank = {uid: pos for pos, uid in enumerate(self.messages)}
        if not self.has_thread:
            # Without the extension, every message is its own thread
            self.threads = [[uid] for uid in self.messages]
            return len(self.threads)
        data = self._cmd(
            "THREAD",
            b"REFERENCES",
            b"UTF-8",
            b"(NOT DELETED)",
            *self.criterions,
        )
        threads = []
        for thread in parse_thread_response(data):
            # A message deleted between the two commands is dropped
            uids = [uid for uid in thread if uid in rank]
            if uids:
                threads.append(uids)
        threads.sort(key=lambda uids: min(rank[uid] for uid in uids))
        self.threads = threads
        return len(self.threads)

    def select_mailbox(
        self, name: str, readonly: bool = True, force: bool = False
    ) -> None:
        """Issue a SELECT/EXAMINE command to the server.

        The given name is first 'imap-utf7' encoded.

        :param name: mailbox's name
        :param readonly:
        """
        if hasattr(self, "current_mailbox"):
            if self.current_mailbox == name and not force:
                return
        self.current_mailbox = name
        name = self._encode_mbox_name(name)
        if readonly:
            self._cmd("EXAMINE", name)
            self.m.is_readonly = True
        else:
            self._cmd("SELECT", name)
        self.m.state = "SELECTED"

    def unseen_messages(self, mailbox: str) -> int:
        """Return the number of unseen messages

        :param mailbox: the mailbox's name
        :return: an integer
        """
        data = self._cmd("STATUS", self._encode_mbox_name(mailbox), "(UNSEEN)")
        m = self.unseen_pattern.match(data[-1].decode())
        if m is None:
            return 0
        return int(m.group(1))

    def _encode_mbox_name(self, folder):
        """Encode folder name (str) to imap4-utf-7 and quote it."""
        if not folder:
            return "INBOX"
        return quote_mailbox_name(folder)

    def _parse_mailbox_name(self, descr, prefix, delimiter, parts):
        if not len(parts):
            return False
        path = f"{prefix}{delimiter}{parts[0]}"
        sdescr = None
        for d in descr:
            if d["path"] == path:
                sdescr = d
                break
        if sdescr is None:
            sdescr = {"name": parts[0], "path": path, "sub": []}
            descr += [sdescr]
        if self._parse_mailbox_name(sdescr["sub"], path, delimiter, parts[1:]):
            sdescr["class"] = "subfolders"
        return True

    def _parse_list_response(self, mb) -> tuple[list, str] | None:
        """Parse a single ``LIST`` response line.

        Handles both the literal form (name returned as a separate
        ``{length}`` string, yielding a ``(header, name)`` tuple) and the
        inline form. Returns the mailbox flags (as a list) and its decoded
        name, or ``None`` for empty lines.
        """
        if not mb:
            return None
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
        name = bytearray(name, "utf-8").decode("imap4-utf-7")
        return flags, name

    @property
    def has_list_status(self) -> bool:
        """Does the server return counters along a LIST reply (RFC 5819)?"""
        return "LIST-STATUS" in getattr(self, "capabilities", [])

    def _collect_unseen_counters(self) -> None:
        """Read the STATUS responses sent along with a LIST reply.

        With the LIST-STATUS extension, one LIST command brings the
        counters of every mailbox back, instead of one STATUS command per
        mailbox.
        """
        for item in self.m.untagged_responses.pop("STATUS", []):
            if isinstance(item, (list, tuple)):
                item = b" ".join(part for part in item if isinstance(part, bytes))
            if isinstance(item, bytes):
                item = item.decode()
            match = self.status_response_pattern.match(item.strip())
            if match is None:
                continue
            unseen = self.status_unseen_pattern.search(match.group("items"))
            if unseen is None:
                continue
            name = bytearray(match.group("name"), "utf-8").decode("imap4-utf-7")
            self._unseen_counters[name] = int(unseen.group(1))

    def _listmboxes(
        self,
        topmailbox: str,
        mailboxes: list,
        until_mailbox=None,
        subscribed_only: bool = False,
    ) -> None:
        """Retrieve mailboxes list."""
        pattern = (
            quote_mailbox_name(f"{topmailbox}{self.hdelimiter}%") if topmailbox else "%"
        )
        returns = ["SUBSCRIBED", "CHILDREN"]
        if self.has_list_status:
            returns.append("STATUS (MESSAGES UNSEEN)")
        resp = self._cmd("LIST", '""', pattern, "RETURN", f"({' '.join(returns)})")
        if self.has_list_status:
            self._collect_unseen_counters()
        newmboxes = []
        for mb in resp:
            parsed = self._parse_list_response(mb)
            if parsed is None:
                continue
            flags, name = parsed
            has_children = "\\HasChildren" in flags
            # When only subscribed mailboxes are requested, skip folders the
            # user is not subscribed to. Unsubscribed folders that still have
            # children are kept so subscribed descendants remain reachable.
            if subscribed_only and "\\Subscribed" not in flags and not has_children:
                continue
            mdm_found = False
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    mdm_found = True
                    descr = mailboxes[idx]
                    break
            if not mdm_found:
                descr = {"name": name, "label": name, "type": "normal"}
                newmboxes += [descr]

            # A mailbox can hold unseen messages without being flagged
            # \Marked (which only tracks messages *recently* added since the
            # last SELECT). To display accurate counters we compute the unseen
            # count for every selectable mailbox instead of relying on that
            # heuristic. \Noselect mailboxes cannot be queried with STATUS.
            descr["selectable"] = "\\Noselect" not in flags
            if r"\NonExistent" in flags:
                descr["removed"] = True
            if has_children:
                descr["path"] = name
                descr["sub"] = []
                if until_mailbox and until_mailbox.startswith(name):
                    self._listmboxes(name, descr["sub"], until_mailbox, subscribed_only)

        from operator import itemgetter

        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    def getmboxes(
        self,
        user,
        topmailbox: str = "",
        until_mailbox=None,
        unseen_messages: bool = True,
        subscribed_only: bool = False,
    ) -> list:
        """Returns a list of mailboxes for a particular user.

        By default, only the first level of mailboxes under
        ``topmailbox`` is returned. If ``until_mailbox`` is specified,
        all levels needed to access this mailbox will be returned.

        :param user: a ``User`` instance
        :param topmailbox: the mailbox where to start in the tree
        :param until_mailbox: the deepest needed mailbox
        :param unseen_messages: include unseen messages counters or not
        :param subscribed_only: only return mailboxes the user is subscribed to
        :return: a list
        """
        if topmailbox:
            md_mailboxes = []
        else:
            md_mailboxes = [
                {"name": "INBOX", "type": "inbox", "label": _("Inbox")},
                {
                    "name": user.parameters.get_value("drafts_folder"),
                    "type": "draft",
                    "label": _("Drafts"),
                },
                {
                    "name": user.parameters.get_value("junk_folder"),
                    "type": "junk",
                    "label": _("Junk"),
                },
                {
                    "name": user.parameters.get_value("sent_folder"),
                    "type": "sent",
                    "label": _("Sent"),
                },
            ]
            if user.scheduledmessage_set.exists():
                md_mailboxes += [
                    {
                        "name": constants.MAILBOX_NAME_SCHEDULED,
                        "type": "scheduled",
                        "label": _("Scheduled"),
                    },
                ]
            md_mailboxes += [
                {
                    "name": user.parameters.get_value("trash_folder"),
                    "type": "trash",
                    "label": _("Trash"),
                },
            ]
        self._unseen_counters = {}
        if until_mailbox:
            name, parent = separate_mailbox(until_mailbox, self.hdelimiter)
            if parent:
                until_mailbox = parent
        self._listmboxes(topmailbox, md_mailboxes, until_mailbox, subscribed_only)
        self._set_unseen_counters(md_mailboxes, unseen_messages)
        return md_mailboxes

    def _set_unseen_counters(self, mailboxes: list, compute: bool = True) -> None:
        """Compute the unseen messages counter of each selectable mailbox.

        The ``selectable`` marker is an internal detail and is always
        removed, whether or not the counters are actually computed.
        """
        for mb in mailboxes:
            selectable = mb.pop("selectable", False)
            if mb.get("sub"):
                self._set_unseen_counters(mb["sub"], compute)
            if not compute or not selectable or mb.get("removed", False):
                continue
            key = "path" if "path" in mb else "name"
            count = self._unseen_counters.get(mb[key])
            if count is None:
                # Server without LIST-STATUS: ask for this mailbox only
                count = self.unseen_messages(mb[key])
            if count:
                mb["unseen"] = count

    def _add_flag(self, mbox: str, msgset: list[str], flag: str) -> None:
        """Add flag to a messages set.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        :param flag: the flag to add
        """
        self.select_mailbox(mbox, False)
        self._cmd("STORE", ",".join(msgset), "+FLAGS", flag)

    def _remove_flag(self, mbox: str, msgset: list[str], flag: str) -> None:
        """Remove flag from a message set.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        :param flag: the flag to remove
        """
        self.select_mailbox(mbox, False)
        self._cmd("STORE", ",".join(msgset), "-FLAGS", flag)

    def mark_messages_unread(self, mbox: str, msgset: list[str]) -> None:
        """Mark a set of messages as unread.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self._remove_flag(mbox, msgset, r"(\Seen)")

    def mark_messages_read(self, mbox: str, msgset: list[str]) -> None:
        """Mark a set of messages as unread.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self._add_flag(mbox, msgset, r"(\Seen)")

    def mark_messages_flagged(self, mbox: str, msgset: list[str]) -> None:
        """Mark a set of messages as flagged.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self._add_flag(mbox, msgset, r"(\Flagged)")

    def mark_messages_unflagged(self, mbox: str, msgset: list[str]) -> None:
        """Mark a set of messages as unflagged.

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self._remove_flag(mbox, msgset, r"(\Flagged)")

    def msg_forwarded(self, mailbox: str, mailid: str) -> None:
        """Add the $Forwarded flag to this email."""
        # _add_flag expects a list: joining a plain string would flag
        # the messages 1, 2, 3 for UID "123".
        self._add_flag(mailbox, [validate_imap_uid(mailid)], "($Forwarded)")

    def msg_answered(self, mailbox: str, mailid: str) -> None:
        """Add the \\Answered flag to this email."""
        self._add_flag(mailbox, [validate_imap_uid(mailid)], r"(\Answered)")

    @property
    def has_move(self) -> bool:
        """Does the server support the MOVE extension (RFC 6851)?"""
        return "MOVE" in getattr(self, "capabilities", [])

    @property
    def has_uidplus(self) -> bool:
        """Does the server support the UIDPLUS extension (RFC 4315)?"""
        return "UIDPLUS" in getattr(self, "capabilities", [])

    def _uid_expunge(self, msgset) -> None:
        """Expunge the given messages, and only them (RFC 4315).

        A plain EXPUNGE would also remove every other message flagged as
        deleted in the mailbox, including those another client of the
        user flagged without wanting to erase them yet.
        """
        try:
            typ, data = self.m.uid("EXPUNGE", msgset)
        except IMAP4Error as e:
            raise ImapError(e) from None
        if typ == "NO":
            raise ImapError(data)

    def move(self, msgset, oldmailbox: str, newmailbox: str) -> None:
        """Move messages between mailboxes.

        MOVE does it with a single atomic command. Without it, messages
        are copied, flagged as deleted, then expunged by UID: leaving
        them behind would keep them visible in other mail clients and
        counted in the user quota.
        """
        self.select_mailbox(oldmailbox, False)
        if self.has_move:
            self._cmd("MOVE", msgset, self._encode_mbox_name(newmailbox))
            return
        self._cmd("COPY", msgset, self._encode_mbox_name(newmailbox))
        self._cmd("STORE", msgset, "+FLAGS", r"(\Deleted \Seen)")
        if self.has_uidplus:
            self._uid_expunge(msgset)

    def push_mail(self, mbox: str, msg) -> int:
        """
        Append a new message to a mailbox.

        Return the UID of the created message.
        """
        now = imaplib.Time2Internaldate(time.time())
        msg = bytes(msg)
        typ, data = self.m.append(self._encode_mbox_name(mbox), r"(\Seen)", now, msg)
        response = data[0].decode()
        m = re.match(r"\[APPENDUID \d+ (\d+)\].+", response)
        if m:
            return int(m.group(1))
        raise WebmailInternalError("Failed to retrieve message UID")

    def delete_mail(self, mbox: str, uid: int) -> None:
        """
        Delete given message (set \Deleted flag) and expunge mailbox.

        Do not use directly.
        """
        uid = validate_imap_uid(uid)
        self.select_mailbox(mbox, False)
        self._cmd("STORE", uid.encode(), "+FLAGS", r"(\Deleted)")
        if self.has_uidplus:
            self._uid_expunge(uid)
        else:
            self._cmd("EXPUNGE")

    def empty(self, mbox: str):
        self.select_mailbox(mbox, False)
        resp = self._cmd("SEARCH", "ALL")
        seq = b",".join(resp[0].split())
        if seq == b"":
            return
        self._cmd("STORE", seq, "+FLAGS", r"(\Deleted)")
        self._cmd("EXPUNGE")

    def compact(self, mbox: str):
        """Compact a specific mailbox.

        Issue an EXPUNGE command for the specified mailbox.

        :param mbox: the mailbox's name
        """
        self.select_mailbox(mbox, False)
        self._cmd("EXPUNGE")

    def _mailbox_command(self, command: str, *args) -> None:
        """Run a mailbox management command (create, rename, delete...).

        The server refusing the operation (NO response) is reported with
        its message; imaplib raises an exception on BAD responses.
        """
        try:
            typ, data = getattr(self.m, command)(*args)
        except IMAP4Error as error:
            raise MailboxOperationError(str(error)) from None
        if typ == "NO":
            raise MailboxOperationError(data[0])

    def create_folder(self, name: str, parent: str | None = None) -> bool:
        if parent is not None:
            name = f"{parent}{self.hdelimiter}{name}"
        self._mailbox_command("create", self._encode_mbox_name(name))
        return True

    def rename_folder(self, oldname: str, newname: str) -> bool:
        self._mailbox_command(
            "rename", self._encode_mbox_name(oldname), self._encode_mbox_name(newname)
        )
        return True

    def delete_folder(self, name: str) -> bool:
        self._mailbox_command("delete", self._encode_mbox_name(name))
        return True

    def get_subscription_tree(self) -> list:
        """Return the full mailbox hierarchy with subscription status.

        Contrary to :meth:`getmboxes`, every folder is returned (regardless
        of subscription) as a nested tree. Each node is a dict with the
        following keys: ``name`` (full path), ``label`` (last path
        component), ``subscribed`` (bool) and ``sub`` (list of children).
        """
        resp = self._cmd("LIST", '""', '"*"', "RETURN", "(SUBSCRIBED)")
        entries = []
        for mb in resp or []:
            parsed = self._parse_list_response(mb)
            if parsed is None:
                continue
            flags, name = parsed
            entries.append((name, "\\Subscribed" in flags))

        tree: list = []
        index: dict = {}
        for name, subscribed in sorted(entries, key=lambda e: e[0]):
            parts = name.split(self.hdelimiter)
            label = parts[-1]
            parent_path = self.hdelimiter.join(parts[:-1])
            node = {
                "name": name,
                "label": label,
                "subscribed": subscribed,
                "sub": [],
            }
            index[name] = node
            parent = index.get(parent_path)
            if parent is not None:
                parent["sub"].append(node)
            else:
                tree.append(node)
        return tree

    def subscribe_folder(self, name: str) -> bool:
        self._mailbox_command("subscribe", self._encode_mbox_name(name))
        return True

    def unsubscribe_folder(self, name: str) -> bool:
        self._mailbox_command("unsubscribe", self._encode_mbox_name(name))
        return True

    def getquota(self, mailbox: str) -> None:
        """Retrieve quota information from the server.

        We also compute the current usage.
        """
        self.quota_limit = self.quota_current = None
        self.quota_usage = -1
        if "QUOTA" not in self.capabilities:
            return
        try:
            data = self._cmd(
                "GETQUOTAROOT",
                self._encode_mbox_name(mailbox),
                responses=["QUOTAROOT", "QUOTA"],
            )
        except ImapError:
            data = None

        if data is None:
            return

        quotadef = data[1][0].decode()
        # A quota root may define other resources (MESSAGE...) along STORAGE
        m = re.search(r"\bSTORAGE (\d+) (\d+)", quotadef)
        if not m:
            logger.warning("Failed to parse quota definition: %s", quotadef)
            return
        self.quota_limit = int(m.group(2))
        self.quota_current = int(m.group(1))
        if self.quota_limit:
            self.quota_usage = int(self.quota_current / self.quota_limit * 100)

    def fetchpart(self, uid: str, mbox: str, partnum):
        """Retrieve a specific message part.

        Useful to fetch attachments from the server. Part headers and
        the payload are returned separatly.

        :param uid: a message UID
        :param mbox: the mailbox containing the message
        :param partnum: the part number
        :return: a 2uple (dict, string)
        """
        uid = validate_imap_uid(uid)
        partnum = validate_imap_partnum(partnum)
        self.select_mailbox(mbox, False)
        data = self._cmd("FETCH", uid, f"(BODYSTRUCTURE BODY[{partnum}])")
        bs = BodyStructure(data[int(uid)]["BODYSTRUCTURE"])
        attdef = bs.find_attachment(partnum)
        return attdef, data[int(uid)][f"BODY[{partnum}]"]

    def fetch(
        self, start: int, stop: int | None = None, mbox: str | None = None
    ) -> list:
        """Retrieve information about messages from the server.

        Issue a FETCH command to retrieve information about one or
        more messages (such as headers) from the server.

        :param start: index of the first message
        :param stop: index of the last message (optionnal)
        :param mbox: the mailbox that contains the messages
        """
        if start and stop:
            submessages = self.messages[start - 1 : stop]
        else:
            submessages = [start]
        return self.fetch_uids(submessages, mbox)

    def fetch_uids(self, uids: list, mbox: str | None = None) -> list:
        """Retrieve the headers of the given messages.

        One FETCH command is issued for the whole list. Messages the
        server does not return (deleted in the meantime) are skipped.

        :param uids: the UIDs to retrieve
        :param mbox: the mailbox that contains the messages
        """
        if not uids:
            return []
        self.select_mailbox(mbox, False)
        mrange = ",".join(str(uid) for uid in uids)
        headers = "DATE FROM TO CC SUBJECT"
        if mbox == constants.MAILBOX_NAME_SCHEDULED:
            headers += " X-SCHEDULED-ID X-SCHEDULED-DATETIME"
        query = (
            f"(FLAGS BODYSTRUCTURE RFC822.SIZE BODY.PEEK[HEADER.FIELDS ({headers})])"
        )
        data = self._cmd("FETCH", mrange, query)
        result = []
        for uid in uids:
            msg_data = data.get(int(uid))
            if msg_data is None:
                logger.debug("Message %s is missing from the FETCH reply", uid)
                continue
            msg = email.message_from_string(
                msg_data[f"BODY[HEADER.FIELDS ({headers})]"]
            )
            msg["imapid"] = uid
            msg["size"] = msg_data["RFC822.SIZE"]
            if r"\Seen" not in msg_data["FLAGS"]:
                msg["style"] = "unseen"
            if r"\Answered" in msg_data["FLAGS"]:
                msg["answered"] = True
            if r"$Forwarded" in msg_data["FLAGS"]:
                msg["forwarded"] = True
            if r"\Flagged" in msg_data["FLAGS"]:
                msg["flagged"] = True
            bstruct = BodyStructure(msg_data["BODYSTRUCTURE"])
            if bstruct.has_attachments():
                msg["attachments"] = True
            result += [msg]
        return result

    def fetch_threads(
        self, start: int, stop: int | None = None, mbox: str | None = None
    ) -> list[dict]:
        """Build a summary of the threads of the given page.

        All the messages of the page are retrieved with a single FETCH,
        through the same code path as the flat listing, so that flags
        and body structures are parsed only once and in one place.

        :param start: index of the first thread
        :param stop: index of the last thread
        :param mbox: the mailbox that contains the messages
        """
        subthreads = self.threads[start - 1 : stop] if start and stop else []
        messages = {
            str(msg["imapid"]): msg
            for msg in self.fetch_uids(
                [uid for thread in subthreads for uid in thread], mbox
            )
        }
        rank = {uid: pos for pos, uid in enumerate(self.messages)}
        result = []
        for thread in subthreads:
            msgs = [messages[uid] for uid in thread if uid in messages]
            if not msgs:
                continue
            # self.messages is ordered from the most recent message to
            # the oldest one, so the latest message has the lowest rank
            latest = min(msgs, key=lambda msg: rank.get(str(msg["imapid"]), 0))
            participants = {}
            for msg in msgs:
                if "From" in msg:
                    address = imapheader.parse_address(msg["From"])
                    participants.setdefault(address["address"], address)
            result.append(
                {
                    "root": str(msgs[0]["imapid"]),
                    # Serializers expect a mapping, not an email.Message
                    "latest": dict(latest),
                    "subject": msgs[0]["Subject"] if "Subject" in msgs[0] else "",
                    "count": len(msgs),
                    "unseen_count": sum(
                        1 for msg in msgs if msg.get("style") == "unseen"
                    ),
                    "flagged": any(msg.get("flagged") for msg in msgs),
                    "attachments": any(msg.get("attachments") for msg in msgs),
                    "participants": list(participants.values()),
                    "uids": [str(msg["imapid"]) for msg in msgs],
                }
            )
        return result

    def fetchmail(
        self, mbox: str, mailid: str, readonly: bool = True, what: str = "bodystructure"
    ):
        """Retrieve information about a specific message.

        Issue a FETCH command to retrieve a message's content from the
        server. In order to not overload the server, we first retrieve
        the BODYSTRUCTURE of the message. Then, according to the
        result and to the user's preferences, we retrieve the
        appropriate content (plain, html, etc.).

        :param mbox: the mailbox containing the message
        :param mailid: the message's unique id
        :param readonly:
        :param headers:
        """
        mailid = validate_imap_uid(mailid)
        self.select_mailbox(mbox, readonly)
        if what == "bodystructure":
            to_fetch = "(BODYSTRUCTURE)"
        elif what == "source":
            to_fetch = "(BODY[])"
        else:
            bcmd = "BODY.PEEK" if readonly else "BODY"
            to_fetch = f"(BODYSTRUCTURE {bcmd}[HEADER.FIELDS ({what})])"
        data = self._cmd("FETCH", mailid, to_fetch)
        if int(mailid) not in data:
            raise ImapError(f"Message with UID {mailid} not found in {mbox} folder")
        return data[int(mailid)]


def separate_mailbox(fullname: str, sep: str = ".") -> tuple[str, str | None]:
    """Split a mailbox name.

    If a separator is found in ``fullname``, this function returns the
    corresponding name and parent mailbox name.
    """
    if sep in fullname:
        parts = fullname.split(sep)
        name = parts[-1]
        parent = sep.join(parts[0 : len(parts) - 1])
        return name, parent
    return fullname, None


CONNECTOR_ATTRIBUTE = "_webmail_imapconnector"


def _connection_store(request):
    """Return the object holding the connector of a request.

    DRF wraps the Django request: always use the underlying one so that
    every caller shares the same connector.
    """
    return getattr(request, "_request", request)


def get_imapconnector(request, **kwargs) -> IMAPconnector:
    """Return the IMAP connector of the given request.

    A single connection is opened per request (and closed by
    :func:`close_imapconnector`) instead of one per operation: each one
    costs a TCP connection, a TLS handshake and an authentication.

    :param request: a ``Request`` object
    """
    if kwargs:
        # Specific settings: not shareable
        return IMAPconnector(
            request.user.username, oauth2.get_access_token(request), **kwargs
        )
    store = _connection_store(request)
    connector = getattr(store, CONNECTOR_ATTRIBUTE, None)
    if connector is None:
        connector = IMAPconnector(
            request.user.username, oauth2.get_access_token(request)
        )
        connector.managed = True
        setattr(store, CONNECTOR_ATTRIBUTE, connector)
    return connector


def close_imapconnector(request) -> None:
    """Close the connector of a request, if one was opened."""
    store = _connection_store(request)
    connector = getattr(store, CONNECTOR_ATTRIBUTE, None)
    if connector is None:
        return
    delattr(store, CONNECTOR_ATTRIBUTE)
    try:
        connector.logout()
    except (ImapError, OSError):
        # The connection is being dropped anyway
        pass
