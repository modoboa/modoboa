# -*- coding: utf-8 -*-

import sys, os
reload(sys)
sys.setdefaultencoding("utf-8")

import re
import time
import socket
import imaplib
import ssl
from datetime import datetime, timedelta
import email.utils
import lxml
from django.utils.translation import ugettext as _
from django.conf import settings
from modoboa.lib import decode, u2u_decode, tables, \
    imap_utf7, static_url, ConnectionsManager, parameters
from modoboa.lib.email_listing import MBconnector, EmailListing, Email

class WebmailError(Exception):
    errorexpr = re.compile("\[([^\]]+)\]\s*([^\.]+)")

    def __init__(self, reason, ajax=False):
        m = WebmailError.errorexpr.match(reason)
        if m is None:
            self.reason = reason
        else:
            self.reason = "%s: %s" % (_("Server response"), m.group(2))
        self.ajax = ajax

    def __str__(self):
        return self.reason

class WMtable(tables.Table):
    tableid = "emails"
    idkey = "imapid"
    _0_select = tables.ImgColumn("select", cssclass="draggable left", width="1%", 
                                 defvalue="%spics/grippy.png" % settings.MEDIA_URL,
                                 header="<input type='checkbox' name='toggleselect' id='toggleselect' />")
    _1_flags = tables.ImgColumn("flags", width="4%")
    _2_subject = tables.Column("subject", label=_("Subject"), width="50%")
    _3_from_ = tables.Column("from", width="20%", label=_("From"))
    _4_date = tables.Column("date", width="20%", label=_("Date"))


    def parse(self, header, value):
        try:
            return getattr(IMAPheader, "parse_%s" % header)(value)
        except AttributeError:
            return value

class EmailAddress(object):
    def __init__(self, address):
        self.fulladdress = u2u_decode.u2u_decode(address).strip("\r\t\n")
        (self.name, self.address) = email.utils.parseaddr(self.fulladdress)
        if self.name == "":
            self.fulladdress = self.address
        
    def __str__(self):
        return self.fulladdress

class IMAPheader(object):
    @staticmethod
    def parse_address(value, **kwargs):
        addr = EmailAddress(value)
        if "full" in kwargs.keys() and kwargs["full"]:
            return addr.fulladdress
        return addr.name and addr.name or addr.fulladdress

    @staticmethod
    def parse_address_list(values, **kwargs):
        lst = values.split(",")
        result = ""
        for addr in lst:
            if result != "":
                result += ", "
            result += IMAPheader.parse_address(addr, **kwargs)
        return result

    @staticmethod
    def parse_from(value, **kwargs):
        return IMAPheader.parse_address(value, **kwargs)

    @staticmethod
    def parse_to(value, **kwargs):
        return IMAPheader.parse_address_list(value, **kwargs)

    @staticmethod
    def parse_cc(value, **kwargs):
        return IMAPheader.parse_address_list(value, **kwargs)

    @staticmethod
    def parse_reply_to(value, **kwargs):
        return IMAPheader.parse_address_list(value, **kwargs)

    @staticmethod
    def parse_date(value, **kwargs):
        tmp = email.utils.parsedate_tz(value)
        if not tmp:
            return value
        ndate = datetime(*(tmp)[:7])
        now = datetime.now()
        try:
            if now - ndate > timedelta(7):
                return ndate.strftime("%d.%m.%Y %H:%M")
            return ndate.strftime("%a %H:%M")
        except ValueError:
            return value


    @staticmethod
    def parse_subject(value, **kwargs):
        return decode(u2u_decode.u2u_decode(value))

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
        import imaplib
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
            # Dovecot stores user scripts into a specific folder, I'm
            # wondering why this folder appears in 'list' result?
            if name in ["dovecot.sieve"]:
                continue
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

    def getfolders(self, user):
        md_folders = [{"name" : "INBOX", "class" : "inbox"},
                      {"name" : parameters.get_user(user, "DRAFTS_FOLDER"), 
                       "class" : "drafts"},
                      {"name" : 'Junk'},
                      {"name" : parameters.get_user(user, "SENT_FOLDER")},
                      {"name" : parameters.get_user(user, "TRASH_FOLDER"),
                       "class" : "trash"}]
        md_folders += self._listfolders(md_folders=md_folders)
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

    def fetch(self, start=None, stop=None, folder=None, all=False):
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

class ImapListing(EmailListing):
    tpl = "webmail/index.html"
    tbltype = WMtable
    deflocation = "INBOX/"
    defcallback = "wm_updatelisting"
    reset_wm_url = False
    
    def __init__(self, user, password, **kwargs):
        self.user = user
        self.mbc = IMAPconnector(user=user.username, password=password)
        if kwargs.has_key("pattern"):
            self.parse_search_parameters(kwargs["criteria"],
                                         kwargs["pattern"])
        if kwargs.has_key("reset"):
            self.mbc.criterions = []
        EmailListing.__init__(self, **kwargs)  
        self.extravars["refreshrate"] = \
            int(parameters.get_user(user, "REFRESH_INTERVAL")) * 1000

    def parse_search_parameters(self, criterion, pattern):
        def or_criterion(old, c):
            if old == "":
                return c
            return "OR (%s) (%s)" % (old, c)
        if criterion == "both":
            criterion = "from_addr, subject"
        criterions = ""
        for c in criterion.split(','):
            if c == "from_addr":
                key = "FROM"
            elif c == "subject":
                key = "SUBJECT"
            else:
                continue
            criterions = \
                unicode(or_criterion(criterions, '%s "%s"' % (key, pattern)))
        self.mbc.criterions = [unicode("(%s)" % criterions)]

    @staticmethod
    def computequota(mbc):
        try:
            return int(float(mbc.quota_actual) \
                           / float(mbc.quota_limit) * 100)
        except (AttributeError, TypeError):
            return -1

    def getquota(self):
        return ImapListing.computequota(self.mbc)

class ImapEmail(Email):
    def __init__(self, msg, user, dformat="DISPLAYMODE", addrfull=False, 
                 *args, **kwargs):
        mformat = parameters.get_user(user, "DISPLAYMODE")
        dformat = parameters.get_user(user, dformat)
        Email.__init__(self, msg, mformat, dformat, *args, **kwargs)

        fields = ["Subject", "From", "To", "Reply-To", "Cc", "Date"]
        for f in fields:
            label = f
            if not f in msg.keys():
                f = f.upper()
                if not f in msg.keys():
                    continue
            try:
                key = re.sub("-", "_", f).lower()
                value = getattr(IMAPheader, "parse_%s" % key)(msg[f], full=addrfull)
                self.headers += [{"name" : label, "value" : value}]
            except AttributeError:
                self.headers += [{"name" : label, "value" : msg[f]}]
            try:
                label = re.sub("-", "_", label)
                setattr(self, label, value)
            except:
                pass

    def render_headers(self, **kwargs):
        from django.template.loader import render_to_string

        res = render_to_string("webmail/headers.html", {
                "headers" : self.headers,
                "folder" : kwargs["folder"], "mail_id" : kwargs["mail_id"],
                "attachments" : self.attachments != {} and self.attachments or None
                })
        return res

class ReplyModifier(ImapEmail):
    def __init__(self, msg, user, form, all=False, **kwargs):
        ImapEmail.__init__(self, msg, user, dformat="EDITOR", **kwargs)

        self.textheader = "%s %s" % (self.From, _("wrote:"))
        getattr(self, "_modify_%s" % self.dformat)()

        form.fields["from_"].initial = user.username
        if not "Reply-To" in msg.keys():
            form.fields["to"].initial = self.From
        else:
            form.fields["to"].initial = self.Reply_To
        if all:
            form.fields["cc"].initial = ""
            toparse = msg["To"].split(",")
            if "Cc" in msg.keys():
                toparse += msg["Cc"].split(",")
            for addr in toparse:
                tmp = EmailAddress(addr)
                if tmp.address and tmp.address == user.username:
                    continue
                if form.fields["cc"].initial != "":
                    form.fields["cc"].initial += ", "
                form.fields["cc"].initial += tmp.fulladdress
        m = re.match("re\s*:\s*.+", self.Subject.lower())
        if m:
            form.fields["subject"].initial = self.Subject
        else:
            form.fields["subject"].initial = "Re: %s" % self.Subject
    
    def _modify_plain(self):
        self.body = re.sub("</?pre>", "", self.body)
        lines = self.body.split('\n')
        body = ""
        for l in lines:
            if body != "":
                body += "\n"
            body += ">%s" % l
        self.body = body

    def _modify_html(self):
        pass

class ForwardModifier(ImapEmail):
    def __init__(self, msg, user, form, **kwargs):
        ImapEmail.__init__(self, msg, user, dformat="EDITOR", **kwargs)
    
        self._header(msg)
        form.fields["from_"].initial = user.username
        form.fields["subject"].initial = "Fwd: %s" % self.Subject

    def __getfunc(self, name):
        return getattr(self, "%s_%s" % (name, self.dformat))

    def _header(self, msg):
        self.textheader = self.__getfunc("_header_begin")() + "\n"
        self.textheader += \
            self.__getfunc("_header_line")(_("Subject"), self.Subject) + "\n"
        self.textheader += \
            self.__getfunc("_header_line")(_("Date"), msg["Date"]) + "\n"
        for hdr in ["From", "To", "Reply-To"]:
            try:
                key = re.sub("-", "_", hdr)
                value = getattr(self, key)
                self.textheader += \
                    self.__getfunc("_header_line")(_(hdr), value) + "\n"
            except:
                pass
        self.textheader += self.__getfunc("_header_end")()

    def _header_begin_plain(self):
        return "----- %s -----" % _("Original message")

    def _header_begin_html(self):
        return  """----- %s -----<br/>
<table border='0'>""" % _("Original message")

    def _header_line_plain(self, key, value):
        return "%s: %s" % (key, value)

    def _header_line_html(self, key, value):
        return "  <tr><td>%s</td><td>%s</td></tr>" % (key, value)

    def _header_end_plain(self):
        return "\n"

    def _header_end_html(self):
        return "</table>"

class EmailSignature(object):
    """User signature

    :param user: User object
    """
    def __init__(self, user):
        dformat = parameters.get_user(user, "EDITOR")
        content = parameters.get_user(user, "SIGNATURE")
        getattr(self, "_format_sig_%s" % dformat)(content)

    def _format_sig_plain(self, content):
        self._sig = """
---
%s""" % content

    def _format_sig_html(self, content):
        content = re.sub("\n", "<br/>", content)
        self._sig = """<br/>
---<br/>
%s""" % content

    def __repr__(self):
        return self._sig

def find_images_in_body(body):
    """Looks for images inside a HTML body

    Before sending a message in HTML format, it is necessary to find
    all img tags contained in the body in order to rewrite them. For
    example, icons provided by CKeditor are stored on the server
    filesystem and not accessible from the outside. We must embark
    them as parts off the MIME message if we want recipients to
    display them correctly.

    :param body: the HTML body to parse
    """
    from email.mime.image import MIMEImage
    from urlparse import urlparse

    html = lxml.html.fromstring(body)
    parts = []
    for tag in html.iter("img"):
        src = tag.get("src")
        if src is None:
            continue
        o = urlparse(src)
        dirname = os.path.dirname(o.path).replace(settings.MEDIA_URL, "")
        fname = os.path.basename(o.path)
        path = os.path.join(settings.MEDIA_ROOT, dirname, fname)
        if not os.path.exists(path):
            continue
        cid = "%s@modoboa" % os.path.splitext(fname)[0]
        tag.set("src", "cid:%s" % cid)
        fp = open(path, "rb")
        p = MIMEImage(fp.read())
        fp.close()
        p["Content-ID"] = "<%s>" % cid
        ct = p["Content-Type"]
        p.replace_header("Content-Type", '%s; name="%s"' \
                             % (ct, os.path.basename(fname)))
        p["Content-Disposition"] = "inline"
        parts.append(p)
        
    return lxml.html.tostring(html), parts
    
