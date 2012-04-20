# coding: utf-8
"""
:mod:`imaputils` --- Extra IMAPv4 utilities
-------------------------------------------
"""
import imaplib, ssl, email
import re
import time
from functools import wraps
from django.utils.translation import ugettext as _
from modoboa.lib import parameters
from modoboa.lib.connections import *
from modoboa.lib.webutils import static_url
from exceptions import ImapError, WebmailError
from fetch_parser import *

#imaplib.Debug = 4

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

class BodyStructure(object):
    """
    BODYSTRUCTURE response parser.

    Just a simple class that tries to distinguish content parts from
    attachments.
    """
    def __init__(self, definition=None):
        self.is_multipart = False
        self.contents = {}
        self.attachments = []
        self.inlines = {}

        if definition is not None:
            self.load_from_definition(definition)

    def __store_part(self, definition, pnum, multisubtype):
        """Store the given message part in the appropriate category.

        This method sort parts in two categories:

        * contents (what is going to be displayed)
        * attachments

        As there is no official definition about what is a content and
        what is an attachment, the following rules are applied:

        * If the MIME type is text/plain or text/html:

         * If no previous part of this type has already been seen, it's a content
         * Otherwise it's an attachment

        * Else, if the multipart subtype is related, we consider this
          part as content because it is certainly an embedded image

        * Any other MIME type is considered as an attachment (for now)

        :param definition: a part definition (list)
        :param prefix: the part's number
        :param multisubtype: the multipart subtype
        """
        pnum = "1" if pnum is None else pnum
        params = dict(pnum=pnum, params=definition[2], cid=definition[3],
                      description=definition[4], encoding=definition[5], 
                      size=definition[6])
        subtype = definition[1].lower()
        mtype = "%s/%s" % (definition[0].lower(), subtype)
        if mtype in ("text/plain", "text/html"):
            if not self.contents.has_key(mtype):
                self.contents[subtype] = params
                return
        elif multisubtype in ["related"]:
            self.inlines[params["cid"].strip("<>")] = params
            return

        if len(definition) > 7:
            params.update(md5=definition[7], disposition=definition[8], 
                          lang=definition[9], location=definition[10])
        self.attachments += [params]

    def load_from_definition(self, definition, multisubtype=None):
        if type(definition) == dict:
            struct = definition["struct"]
            pnum = definition["partnum"]
        elif type(definition[0]) == dict:
            struct = definition[0]["struct"]
            pnum = definition[0]["partnum"]
        else:
            struct = definition
            pnum = None

        if type(struct[0]) == list:
            for part in struct[0]:
                self.load_from_definition(part, struct[1])
            return
        
        self.__store_part(struct, pnum, multisubtype)

    def has_attachments(self):
        return len(self.attachments)

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
        if not kwargs.has_key('responses'):
            if not name in self.m.untagged_responses:
                return None
            return self.m.untagged_responses.pop(name)
        res = []
        for r in kwargs['responses']:
            if not r in self.m.untagged_responses:
                return None
            res.append(self.m.untagged_responses.pop(r))
        return res

    def __find_content_in_bodystruct(self, bodystruct, mtype, stype, prefix=""):
        """Retrieve the number (index) of a specific part

        This part number will generally be used inside a FETCH request
        to specify a ``BODY.PEEK`` section.

        :param bodystruct: a BODYSTRUCTURE list
        :param mtype: the MIME main type (like text)
        :param stype: the MIME sub type (like plain)
        :param prefix: the prefix that will be added to the current part number
        :return: a tuple (index (None on error), encoding (string), size (int))
        """
        if type(bodystruct[0]) in [list, tuple]:
            cpt = 1
            for part in bodystruct[0]:
                nprefix = "%s" % cpt if prefix == "" else "%s.%d" % (prefix, cpt)
                index, encoding, size = \
                    self.__find_content_in_bodystruct(part, mtype, stype, nprefix)
                if index is not None:
                    return (index, encoding, size)
                cpt += 1
        else:
            if bodystruct[0].lower() == mtype and bodystruct[1].lower() == stype:
                return ("1" if not len(prefix) else prefix, 
                        bodystruct[5], int(bodystruct[6]))
        return (None, None, 0)

    def refresh(self, user, password):
        """Check if current connection needs a refresh

        Is it really secure?
        """
        if self.m is not None:
            try:
                self._cmd("CHECK")
            except ImapError, e:
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
        try:
            secured = parameters.get_admin("IMAP_SECURED")
            if secured == "yes":
                self.m = imaplib.IMAP4_SSL(self.address, self.port)
            else:
                self.m = imaplib.IMAP4(self.address, self.port)
        except (socket.error, imaplib.IMAP4.error, ssl.SSLError), error:
            raise ImapError(_("Connection to IMAP server failed: %s" % error))

        data = self._cmd("LOGIN", user, passwd)
        self.m.state = "AUTH"
        if self.m.untagged_responses.has_key("CAPABILITY"):
            self.capabilities = \
                self.m.untagged_responses.pop('CAPABILITY')[0].split()
        else:
            data = self._cmd("CAPABILITY")
            self.capabilities = data[0].split()

    def logout(self):
        try:
            self._cmd("CHECK")
        except ImapError, e:
            pass
        self._cmd("LOGOUT")
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

        # FIXME: pourquoi suis je obligé de faire un SELECT ici?  un
        # EXAMINE plante mais je pense que c'est du à une mauvaise
        # lecture des réponses de ma part...
        self.select_mailbox(folder, readonly=False)
        data = self._cmd("SORT", "(%s)" % criterion, "UTF-8", "(NOT DELETED)",
                         *self.criterions)
        self.messages = data[0].split()
        self.getquota(folder)
        return len(self.messages)

    def select_mailbox(self, name, readonly=True, force=False):
        """Issue a SELECT/EXAMINE command to the server

        The given name is first 'imap-utf7' encoded.
        
        :param name: mailbox's name
        :param readonly: 
        """
        if hasattr(self, "current_mailbox"):
            if self.current_mailbox == name and not force:
                return
        self.current_mailbox = name
        name = name.encode("imap4-utf-7")
        if readonly:
            self._cmd("EXAMINE", name)
        else:
            self._cmd("SELECT", name)
        self.m.state = "SELECTED"

    def unseen_messages(self, mailbox):
        """Return the number of unseen messages

        :param mailbox: the mailbox's name
        :return: an integer
        """
        data = self._cmd("STATUS", mailbox.encode("imap4-utf-7"), "(UNSEEN)")
        m = self.unseen_pattern.match(data[-1])
        if m is None:
            return 0
        return int(m.group(1))

    def _encode_mbox_name(self, folder):
        if not folder:
            return "INBOX"
        return folder.encode("imap4-utf-7")

    def _parse_mailbox_name(self, descr, prefix, delimiter, parts):
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
        if self._parse_mailbox_name(sdescr["sub"], path, delimiter, parts[1:]):
            sdescr["class"] = "subfolders"
        return True

    def _listmboxes_simple(self, topmailbox='INBOX', mailboxes=[], **kwargs):
        #data = self._cmd("LIST", "", "*")
        (status, data) = self.m.list()
        result = []
        newmboxes = []
        for mb in data:
            flags, delimiter, name = self.list_response_pattern.match(mb).groups()
            name = name.strip('"').decode("imap4-utf-7")
            pos = -1
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    pos = idx
                    break
            if pos == -1:
                descr = dict(name=name)
                newmboxes += [descr]
            else:
                descr = mailboxes[idx]
            if re.search("\%s" % delimiter, name):
                parts = name.split(".")
                if not descr.has_key("path"):
                    descr["path"] = parts[0]
                    descr["sub"] = []
                if self._parse_mailbox_name(descr["sub"], parts[0], delimiter, 
                                            parts[1:]):
                    descr["class"] = "subfolders"
                continue

        from operator import itemgetter
        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    @capability('LIST-EXTENDED', '_listmboxes_simple')
    def _listmboxes(self, topmailbox='', mailboxes=[], until_mailbox=None):
        pattern = ("%s.%%" % topmailbox.encode("imap4-utf-7")) if len(topmailbox) else "%"
        resp = self._cmd("LIST", "", pattern, "RETURN", "(CHILDREN)")
        newmboxes = []
        for mb in resp:
            flags, delimiter, name, childinfo = \
                self.listextended_response_pattern.match(mb).groups()
            flags = flags.split(' ')
            name = name.decode("imap4-utf-7")
            pos = -1
            for idx, mdm in enumerate(mailboxes):
                if mdm["name"] == name:
                    pos = idx
                    break
            if pos == -1:
                descr = dict(name=name)
                newmboxes += [descr]
            else:
                descr = mailboxes[idx]
            
            if r'\Marked' in flags or not r'\UnMarked' in flags:
                descr["send_status"] = True
            if r'\HasChildren' in flags:
                descr["path"] = name
                descr["sub"] = []
                if until_mailbox and until_mailbox.startswith(name):
                    self._listmboxes(name, descr["sub"], until_mailbox)

        from operator import itemgetter
        mailboxes += sorted(newmboxes, key=itemgetter("name"))

    def getmboxes(self, user, topmailbox='', until_mailbox=None, unseen_messages=True):
        """Returns a list of mailboxes for a particular user

        By default, only the first level of mailboxes under
        ``topmailbox`` is returned. If ``until_mailbox`` is specified,
        all levels needed to access this mailbox will be returned.

        :param user: a ``User`` instance
        :param topmailbox: the mailbox where to start in the tree
        :param until_mailbox: the deepest needed mailbox
        :param unseen_messages: include unseen messages counters or not
        :return: a list
        """
        if len(topmailbox):
            md_mailboxes = []
        else:
            md_mailboxes = [{"name" : "INBOX", "class" : "icon-home"},
                            {"name" : parameters.get_user(user, "DRAFTS_FOLDER"), 
                             "class" : "icon-file"},
                            {"name" : 'Junk'},
                            {"name" : parameters.get_user(user, "SENT_FOLDER")},
                            {"name" : parameters.get_user(user, "TRASH_FOLDER"),
                             "class" : "icon-trash"}]
        if until_mailbox:
            name, parent = separate_mailbox(until_mailbox)
            if parent:
                until_mailbox = parent
        self._listmboxes(topmailbox, md_mailboxes, until_mailbox)

        if unseen_messages:
            for mb in md_mailboxes:
                if not mb.has_key("send_status"):
                    continue
                del mb["send_status"]
                key = mb.has_key("path") and "path" or "name"
                count = self.unseen_messages(mb[key])
                if count == 0:
                    continue
                mb["unseen"] = count
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

    def msg_forwarded(self, mailbox, mailid):
        self._add_flag(mailbox, mailid, '($Forwarded)')

    def msg_answered(self, mailbox, mailid):
        """Add the \Answered flag to this email"""
        self._add_flag(mailbox, mailid, r'(\Answered)')

    def move(self, msgset, oldmailbox, newmailbox):
        """Move messages between mailboxes

        """
        self.select_mailbox(oldmailbox, False)
        self._cmd("COPY", msgset, newmailbox.encode("imap4-utf-7"))
        self._cmd("STORE", msgset, "+FLAGS", r'(\Deleted \Seen)')

    def push_mail(self, folder, msg):
        now = imaplib.Time2Internaldate(time.time())
        self.m.append(self._encode_mbox_name(folder), r'(\Seen)', now, str(msg))

    def empty(self, mbox):
        self.select_mailbox(mbox, False)
        resp = self._cmd("SEARCH", "ALL")
        seq = ",".join(resp[0].split())
        self._cmd("STORE", seq, "+FLAGS", r'(\Deleted)')
        self._cmd("EXPUNGE")

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
        typ, data = self.m.create(self._encode_mbox_name(name))
        if typ == "NO":
            raise WebmailError(data[0])
        return True

    def rename_folder(self, oldname, newname):
        typ, data = self.m.rename(self._encode_mbox_name(oldname),
                                  self._encode_mbox_name(newname))
        if typ == "NO":
            raise WebmailError(data[0], ajax=True)
        return True

    def delete_folder(self, name):
        typ, data = self.m.delete(self._encode_mbox_name(name))
        if typ == "NO":
            raise WebmailError(data[0])
        return True

    def getquota(self, mailbox):
        if not "QUOTA" in self.capabilities:
            self.quota_limit = self.quota_actual = None
            return

        data = self._cmd("GETQUOTAROOT", self._encode_mbox_name(mailbox), 
                         responses=["QUOTAROOT", "QUOTA"])
        if data is None:
            self.quota_limit = self.quota_actual = None
            return
        
        quotadef = data[1][0]
        m = re.match("[^\s]+ \(STORAGE (\d+) (\d+)\)", quotadef)
        if not m:
            print "Problem while parsing quota def"
            return
        self.quota_limit = int(m.group(2))
        self.quota_actual = int(m.group(1))

    def fetchpart(self, uid, mbox, partnum):
        self.select_mailbox(mbox, False)
        data = self._cmd("FETCH", uid, "(BODY[%s])" % partnum)
        return data[int(uid)]["BODY[%s]" % partnum]

    def fetch(self, start, stop=None, mbox=None, **kwargs):
        """Retrieve information about messages from the server

        Issue a FETCH command to retrieve information about one or
        more messages (such as headers) from the server.

        :param start: index of the first message
        :param stop: index of the last message (optionnal)
        :param mbox: the mailbox that contains the messages
        """
        self.select_mailbox(mbox, False)
        if start and stop:
            submessages = self.messages[start - 1:stop]
            range = ",".join(submessages)
        else:
            submessages = [start]
            range = start
        query = '(FLAGS BODYSTRUCTURE BODY.PEEK[HEADER.FIELDS (DATE FROM TO CC SUBJECT)])'
        data = self._cmd("FETCH", range, query)
        result = []
        for uid in submessages:
            msg = email.message_from_string(data[int(uid)]['BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)]'])
            msg['imapid'] = uid
            if not r'\Seen' in data[int(uid)]['FLAGS']:
                msg['style'] = 'unseen'
            if r'\Answered' in data[int(uid)]['FLAGS']:
                msg['img_flags'] = static_url('pics/answered.png')
            if r'$Forwarded' in data[int(uid)]['FLAGS']:
                msg['img_flags'] = static_url('pics/forwarded.png')
            bs = BodyStructure(data[int(uid)]['BODYSTRUCTURE'])
            if bs.has_attachments():
                msg['img_withatts'] = static_url('pics/attachment.png')
            result += [msg]
        return result

    def fetchmail(self, mbox, mailid, readonly=True, headers=None):
        """Retrieve information about a specific message

        Issue a FETCH command to retrieve a message's content from the
        server. In order to not overload the server, we first retrieve
        the BODYSTRUCTURE of the message. Then, according to the
        result and to the user's preferences, we retrieve the
        appropriate content (plain, html, etc.).

        :param mbox: the mailbox containing the message
        :param mailid: the message's unique id
        :param readonly:
        :param extraheaders:
        """
        print mbox
        self.select_mailbox(mbox, readonly)
        if headers is None:
            headers = ['DATE', 'FROM', 'TO', 'CC', 'SUBJECT']
        bcmd = "BODY.PEEK" if readonly else "BODY"
        data = self._cmd(
            "FETCH", mailid, 
            "(BODYSTRUCTURE %s[HEADER.FIELDS (%s)])" % (bcmd, " ".join(headers))
            )
        return data[int(mailid)]

def separate_mailbox(fullname, sep="."):
    """Split a mailbox name

    If a separator is found in ``fullname``, this function returns the
    corresponding name and parent mailbox name.
    """
    if fullname.count("."):
        parts = fullname.split(sep)
        name = parts[-1]
        parent = sep.join(parts[0:len(parts) - 1])
        return name, parent
    return fullname, None

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

