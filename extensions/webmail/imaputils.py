# coding: utf-8
"""
:mod:`imaputils` --- Extra IMAPv4 utilities
-------------------------------------------
"""
import imaplib, ssl, email
import re
from functools import wraps
from imapclient.response_parser import parse_fetch_response
from modoboa.lib import parameters
from modoboa.lib.connections import *
from modoboa.lib.webutils import static_url
from exceptions import ImapError

imaplib.Debug = 4

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
            if self.name in cls.m.capabilities:
                return method(cls, *args, **kwargs)
            return getattr(cls, self.fallback_method)(*args, **kwargs)

        return wrapped_func


class IMAPconnector(object):
    __metaclass__ = ConnectionsManager

    list_base_pattern = r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" "(?P<name>[^"]*)"'
    list_response_pattern = re.compile(list_base_pattern)
    listextended_response_pattern = \
        re.compile(list_base_pattern + r'\s*(?P<childinfo>.*)')
    unseen_pattern = re.compile(r'[^\(]+\(UNSEEN (\d+)\)')

    def __init__(self, user=None, password=None):
        self.criterions = []
        self.address = parameters.get_admin("IMAP_SERVER")
        self.port = int(parameters.get_admin("IMAP_PORT"))
        status, msg = self.login(user, password)
        if not status:
            raise Exception(msg)

    def _cmd(self, name, *args):
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
        if name in ['FETCH', 'SORT', 'STORE', 'COPY']:
            try:
                typ, data = self.m.uid(name, *args)
            except imaplib.IMAP4.error, e:
                raise ImapError(e)
            if typ == "NO":
                raise ImapError(data)
            if name == 'FETCH':
                return parse_fetch_response(data)
            return data

        try:
            typ, data = self.m._simple_command(name, *args)
        except imaplib.IMAP4.error, e:
            raise ImapError(e)
        if typ == "NO":
            raise ImapError(data)
        if not name in self.m.untagged_responses:
            return None
        return self.m.untagged_responses.pop(name)

    def refresh(self, user, password):
        """Check if current connection needs a refresh

        Is it really secure?
        """
        if self.m is not None:
            try:
                self.m.select()
                return
            except imaplib.IMAP4.error, error:
                print error          
        print self.login(user, password)


    def login(self, user, passwd):
        try:
            secured = parameters.get_admin("IMAP_SECURED")
            if secured == "yes":
                self.m = imaplib.IMAP4_SSL(self.address, self.port)
            else:
                self.m = imaplib.IMAP4(self.address, self.port)
        except (socket.error, imaplib.IMAP4.error, ssl.SSLError), error:
            return False, _("Connection to IMAP server failed, check your configuration")
        try:
            self.m.login(user, passwd)
        except (imaplib.IMAP4.error, ssl.SSLError), error:
            return False, _("Authentication failed, check your configuration")
        return True, None

    def logout(self):
        try:
            self.m.select()
        except imaplib.IMAP4.error:
            pass
        self.m.logout()
        del self.m
        self.m = None

    def messages_count(self, **kwargs):
        """An enhanced version of messages_count

        With IMAP, to know how many messages a mailbox contains, we
        have to make a request to the server. To avoid requests
        multiplications, we sort messages in the same time. This will
        be usefull for other methods.

        :param order: sorting order
        :param folder: mailbox to scan
        """
        if "order" in kwargs.keys() and kwargs["order"]:
            sign = kwargs["order"][:1]
            criterion = kwargs["order"][1:].upper()
            if sign == '-':
                criterion = "REVERSE %s" % criterion
        else:
            criterion = "REVERSE DATE"
        folder = kwargs.has_key("folder") and kwargs["folder"] or None
        self.select_mailbox(folder, False)
        data = self._cmd("SORT", "(%s)" % criterion, "UTF-8", "(NOT DELETED)",
                         *self.criterions)
        self.messages = data[0].split()
        self.getquota(folder)
        return len(self.messages)

    def select_mailbox(self, name, readonly=True):
        """Issue a SELECT/EXAMINE command to the server

        The given name is first 'imap-utf7' encoded.
        
        :param name: mailbox's name
        :param readonly: 
        """
        name = name.encode("imap4-utf-7")
        if readonly:
            self._cmd("EXAMINE", name)
        else:
            self._cmd("SELECT", name)

    def unseen_messages(self, mailbox):
        """Return the number of unseen messages

        :param mailbox: the mailbox's name
        :return: an integer
        """
        # self.select_mailbox(mailbox)
        # data = self._cmd("SEARCH", "UTF-8", "(NOT DELETED UNSEEN)")
        # return len(data[0].split())
        data = self._cmd("STATUS", mailbox.encode("imap4-utf-7"), "(UNSEEN)")
        m = self.unseen_pattern.match(data[0])
        if m is None:
            return 0
        return int(m.group(1))

    def _encodefolder(self, folder):
        if not folder:
            return "INBOX"
        return folder.encode("imap4-utf-7")

    def _parse_folder_name(self, descr, prefix, delimiter, parts):
        if not len(parts):
            return False
        path = "%s%s%s" % (prefix, delimiter, parts[0])
        sdescr = None
        for d in descr:
            if d["path"] == path:
                sdescr = d
                break
        if sdescr is None:
            sdescr = {"name" : parts[0], "path" : path, "sub" : []}
            descr += [sdescr]            
        if self._parse_folder_name(sdescr["sub"], path, delimiter, parts[1:]):
            sdescr["class"] = "subfolders"
        return True

    def _listfolders_simple(self, topmailbox='INBOX', md_mailboxes=[]):
        (status, data) = self.m.list()
        result = []
        for mb in data:
            flags, delimiter, name = self.list_response_pattern.match(mb).groups()
            name = name.strip('"').decode("imap4-utf-7")
            if re.search("\%s" % delimiter, name):
                parts = name.split(".")
                if not descr.has_key("path"):
                    descr["path"] = parts[0]
                    descr["sub"] = []
                if self._parse_folder_name(descr["sub"], parts[0], delimiter, 
                                           parts[1:]):
                    descr["class"] = "subfolders"
                continue
            present = False
            descr = {"name" : name}
            for mdf in md_mailboxes:
                if mdf["name"] == name:
                    present = True
                    break
            if not present:
                result += [descr]
        from operator import itemgetter
        return sorted(result, key=itemgetter("name"))

    @capability('LIST-EXTENDED', '_listfolders_simple')
    def _listfolders(self, topmailbox='', md_mailboxes=[]):
        pattern = ("%s.%%" % topmailbox.encode("imap4-utf-7")) if len(topmailbox) else "%"
        resp = self._cmd("LSUB", "", pattern, "RETURN", "(CHILDREN)")
        result = []
        for mb in resp:
            flags, delimiter, name, childinfo = \
                self.listextended_response_pattern.match(mb).groups()
            flags = flags.split(' ')
            name = name.decode("imap4-utf-7")
            present = False
            for mdm in md_mailboxes:
                if mdm["name"] == name:
                    present = True
                    break
            if present:
                continue
            descr = dict(name=name)
            if r'\HasChildren' in flags:
                descr["path"] = name
                descr["sub"] = []
                descr["class"] = "subfolders"
            result += [descr]
        from operator import itemgetter
        return sorted(result, key=itemgetter("name"))

    def getfolders(self, user, topmailbox='', unseen_messages=True):
        if len(topmailbox):
            md_mailboxes = []
        else:
            md_mailboxes = [{"name" : "INBOX", "class" : "inbox"},
                            {"name" : parameters.get_user(user, "DRAFTS_FOLDER"), 
                             "class" : "drafts"},
                            {"name" : 'Junk'},
                            {"name" : parameters.get_user(user, "SENT_FOLDER")},
                            {"name" : parameters.get_user(user, "TRASH_FOLDER"),
                             "class" : "trash"}]
        md_mailboxes += self._listfolders(topmailbox, md_mailboxes)
        if unseen_messages:
            for fd in md_mailboxes:
                key = fd.has_key("path") and "path" or "name"
                count = self.unseen_messages(fd[key])
                if count == 0:
                    continue
                fd["unseen"] = count
        return md_mailboxes

    def _add_flag(self, mbox, msgset, flag):
        """Add flag(s) to a messages set

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        :param flag: the flag to add
        """
        self.select_mailbox(mbox, False)
        self._cmd("STORE", msgset, "+FLAGS", flag)

    def mark_messages_unread(self, mbox, msgset):
        """Mark a set of messages as unread

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self.select_mailbox(mbox, False)
        self._cmd("STORE", msgset, "-FLAGS", r'(\Seen)')

    def mark_messages_read(self, mbox, msgset):
        """Mark a set of messages as unread

        :param mbox: the mailbox containing the messages
        :param msgset: messages set (uid)
        """
        self._add_flag(mbox, msgset, r'(\Seen)')

    def msgforwarded(self, folder, imapid):
        self._add_flag(folder, imapid, '($Forwarded)')

    def msg_answered(self, folder, imapid):
        self._add_flag(folder, imapid, r'(\Answered)')

    def move(self, msgset, oldmailbox, newmailbox):
        """Move messages between mailboxes

        """
        self.select_mailbox(oldmailbox, False)
        self._cmd("COPY", msgset, newmailbox.encode("imap4-utf-7"))
        self._cmd("STORE", msgset, "+FLAGS", r'(\Deleted)')

    def push_mail(self, folder, msg):
        now = imaplib.Time2Internaldate(time.time())
        self.m.append(self._encodefolder(folder), r'(\Seen)', now, str(msg))

    def empty(self, mbox):
        self.select_mailbox(mbox, False)
        resp = self._cmd("SEARCH", "ALL")
        print resp
        
        # for num in data[0].split():
        #     self.m.store(num, "+FLAGS", r'(\Deleted)')
        # self.m.expunge()

    def compact(self, mbox):
        """Compact a specific mailbox

        Issue an EXPUNGE command for the specified mailbox.
        
        :param mbox: the mailbox's name
        """
        self.select_mailbox(mbox, False)
        self._cmd("EXPUNGE")

    def create_folder(self, name, parent=None):
        if parent is not None:
            name = "%s.%s" % (parent, name)
        typ, data = self.m.create(self._encodefolder(name))
        if typ == "NO":
            raise WebmailError(data[0])
        return True

    def rename_folder(self, oldname, newname):
        typ, data = self.m.rename(self._encodefolder(oldname),
                                  self._encodefolder(newname))
        if typ == "NO":
            raise WebmailError(data[0], ajax=True)
        return True

    def delete_folder(self, name):
        typ, data = self.m.delete(self._encodefolder(name))
        if typ == "NO":
            raise WebmailError(data[0])
        return True

    def getquota(self, folder):
        if not "QUOTA" in self.m.capabilities:
            self.quota_limit = self.quota_actual = None
            return

        status, data = self.m.getquotaroot(self._encodefolder(folder))
        if status == "OK":
            quotadef = data[1][0]
            m = re.match("[^\s]+ \(STORAGE (\d+) (\d+)\)", quotadef)
            if not m:
                print "Problem while parsing quota def"
                return
            self.quota_limit = int(m.group(2))
            self.quota_actual = int(m.group(1))

    def fetchpart(self, uid, folder, part):
        self.m.select(self._encodefolder(folder), True)
        typ, data = self.m.fetch(uid, "(BODY[%(p)s.MIME] BODY[%(p)s])" \
                                     % {"p" : part})
        if typ != "OK":
            return None
        msg = email.message_from_string(data[0][1] + data[1][1])
        return msg

    def fetch(self, start, stop=None, folder=None, all=False, **kwargs):
        self.select_mailbox(folder, False)
        if start and stop:
            submessages = self.messages[start - 1:stop]
            range = ",".join(submessages)
        else:
            submessages = [start]
            range = start
        if not all:
            query = '(FLAGS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM TO CC SUBJECT)])'
        else:
            query = '(RFC822)'
        data = self._cmd("FETCH", range, query)
        result = []
        for uid in submessages:
            msg = email.message_from_string(data[int(uid)]['BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)]'])
            msg['imapid'] = uid
            if not r'\Seen' in data[int(uid)]['FLAGS']:
                msg['class'] = 'unseen'
            if r'\Answered' in data[int(uid)]['FLAGS']:
                msg['img_flags'] = static_url('pics/answered.png')
            result += [msg]
        return result

def get_imapconnector(request):
    imapc = IMAPconnector(user=request.user.username, 
                          password=request.session["password"])
    return imapc
