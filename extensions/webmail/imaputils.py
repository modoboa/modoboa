# coding: utf-8
"""
:mod:`imaputils` --- Extra IMAPv4 utilities
-------------------------------------------
"""
import imaplib, ssl, email
import re
from modoboa.lib import parameters
from modoboa.lib.connections import *
from modoboa.lib.webutils import static_url

class IMAPconnector(object):
    __metaclass__ = ConnectionsManager

    def __init__(self, user=None, password=None):
        self.criterions = []
        self.address = parameters.get_admin("IMAP_SERVER")
        self.port = int(parameters.get_admin("IMAP_PORT"))
        status, msg = self.login(user, password)
        if not status:
            raise Exception(msg)

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
        (status, data) = self.m.select(self._encodefolder(folder))
        (status, data) = self.m.sort("(%s)" % criterion, "UTF-8", "(NOT DELETED)",
                                     *self.criterions)
        self.messages = data[0].split()
        self.getquota(folder)
        return len(self.messages)

    def unseen_messages(self, folder):
        """Return the number of unseen messages for folder"""
        self.m.select(self._encodefolder(folder), True)
        status, data = self.m.search("UTF-8", "(NOT DELETED UNSEEN)")
        if status != "OK":
            return
        return len(data[0].split())

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

    def _listfolders(self, topfolder='INBOX', md_folders=[]):
        list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
        (status, data) = self.m.list()
        result = []
        for mb in data:
            flags, delimiter, name = list_response_pattern.match(mb).groups()
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
            for mdf in md_folders:
                if mdf["name"] == name:
                    present = True
                    break
            if not present:
                result += [descr]
        from operator import itemgetter
        return sorted(result, key=itemgetter("name"))

    def getfolders(self, user, unseen_messages=True):
        md_folders = [{"name" : "INBOX", "class" : "inbox"},
                      {"name" : parameters.get_user(user, "DRAFTS_FOLDER"), 
                       "class" : "drafts"},
                      {"name" : 'Junk'},
                      {"name" : parameters.get_user(user, "SENT_FOLDER")},
                      {"name" : parameters.get_user(user, "TRASH_FOLDER"),
                       "class" : "trash"}]
        md_folders += self._listfolders(md_folders=md_folders)
        if unseen_messages:
            for fd in md_folders:
                key = fd.has_key("path") and "path" or "name"
                count = self.unseen_messages(fd[key])
                if count == 0:
                    continue
                fd["unseen"] = count
        return md_folders

    def _add_flag(self, folder, mail_id, flag):
        self.m.select(self._encodefolder(folder))
        self.m.store(mail_id, "+FLAGS", flag)

    def msg_unread(self, folder, msgset):
        self.m.select(self._encodefolder(folder))
        self.m.store(msgset, "-FLAGS", r'(\Seen)')

    def msg_read(self, folder, msgset):
        self._add_flag(folder, msgset, r'(\Seen)')

    def msgforwarded(self, folder, imapid):
        self._add_flag(folder, imapid, '($Forwarded)')

    def msg_answered(self, folder, imapid):
        self._add_flag(folder, imapid, r'(\Answered)')

    def move(self, msgset, oldfolder, newfolder):
        self.m.select(self._encodefolder(oldfolder))
        status, data = self.m.copy(msgset, self._encodefolder(newfolder))
        if status == 'OK':
            self.m.store(msgset, "+FLAGS", r'(\Deleted)')

    def push_mail(self, folder, msg):
        now = imaplib.Time2Internaldate(time.time())
        self.m.append(self._encodefolder(folder), r'(\Seen)', now, str(msg))

    def empty(self, folder):
        self.m.select(self._encodefolder(folder))
        typ, data = self.m.search(None, 'ALL')
        for num in data[0].split():
            self.m.store(num, "+FLAGS", r'(\Deleted)')
        self.m.expunge()

    def compact(self, folder):
        self.m.select(self._encodefolder(folder))
        self.m.expunge()

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

    def fetch(self, start=None, stop=None, folder=None, all=False, **kwargs):
        if not start and not stop:
            return []
        result = []
        self.m.select(self._encodefolder(folder), True)
        if start and stop:
            submessages = self.messages[start - 1:stop]
            range = ",".join(submessages)
        else:
            submessages = [start]
            range = start
        if not all:
            query = '(FLAGS BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)])'
        else:
            query = '(RFC822)'
        typ, data = self.m.fetch(range, query)
        if not folder:
            folder = "INBOX"
        tmpdict = {}

        for response_part in data:
            if isinstance(response_part, tuple):
                imapid = response_part[0].split()[0]
                flags = imaplib.ParseFlags(response_part[0])
                msg = email.message_from_string(response_part[1])
                msg["imapid"] = imapid
                if not "\\Seen" in flags:
                    msg["class"] = "unseen"
                if "\\Answered" in flags:
                    msg["img_flags"] = static_url("pics/answered.png")
                tmpdict[imapid] = msg
        for id in submessages:
            result += [tmpdict[id]]
        return result

def get_imapconnector(request):
    imapc = IMAPconnector(user=request.user.username, 
                          password=request.session["password"])
    return imapc
