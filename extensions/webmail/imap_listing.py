
# -*- coding: utf-8 -*-

import re
import time
import imaplib
#import ssl
from datetime import datetime, timedelta
from email.header import decode_header
import email.utils
from django.utils.translation import ugettext as _
from mailng.lib import decode, tables, imap_utf7, Singleton
from mailng.lib.email_listing import MBconnector, EmailListing, Email
from mailng.lib import tables, imap_utf7, parameters


class WMtable(tables.Table):
    tableid = "emails"
    idkey = "imapid"
#    selection = tables.SelectionColumn("selection", width="20px", first=True)
    _1_flags = tables.ImgColumn("flags", width="4%",
                                header="<input type='checkbox' name='toggleselect' id='toggleselect' />")
    _2_subject = tables.Column("subject", label=_("Subject"), 
                               cssclass="draggable", width="50%")
    _3_from_ = tables.Column("from", width="20%", label=_("From"))
    _4_date = tables.Column("date", width="20%", label=_("Date"))


    def parse(self, header, value):
        try:
            return getattr(IMAPheader, "parse_%s" % header)(value)
        except AttributeError:
            return value

class EmailAddress(object):
    addr_exp = re.compile("([^<\(]+)[<(]([^>)]+)[>)]")
    name_exp = re.compile('"([^"]+)"')

    def __init__(self, address):
        self.fulladdress = address
        self.name = self.address = None
        m = EmailAddress.addr_exp.match(self.fulladdress)
        if m is None:
            return
        name = m.group(1).strip()
        self.address = m.group(2).strip()
        m2 = EmailAddress.name_exp.match(name)
        if m2:
            name = m2.group(1)
        self.name = ""
        for part in decode_header(name):
            if self.name != "":
                self.name += " "
            if part[1] is None:
                self.name += part[0]
            else:
                self.name += unicode(part[0], part[1])
        self.fulladdress = "%s <%s>" % (self.name, self.address)

    def __str__(self):
        return self.fulladdress

class IMAPheader(object):
    @staticmethod
    def parse_address(value, **kwargs):
        addr = EmailAddress(value)
        if "full" in kwargs.keys() and kwargs["full"]:
            return addr.fulladdress
        return addr.name and addr.name or value

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
        res = ""
        dcd = decode_header(value)
        for part in dcd:
            if res != "":
                res += " "
            res += part[0].strip(" ")
        return decode(res)

class IMAPconnector(object):
    __metaclass__ = Singleton

    def __init__(self, request=None, user=None, password=None):
        self.criterions = []
        self.address = parameters.get("webmail", "IMAP_SERVER")
        self.port = int(parameters.get("webmail", "IMAP_PORT"))
        if request:
            status, msg = self.login(request.user.username, 
                                     request.session["password"])
        else:
            status, msg = self.login(user, password)
        if not status:
            raise Exception(msg)

    def login(self, user, passwd):
        import imaplib
        try:
            secured = parameters.get("webmail", "IMAP_SECURED")
            if secured == "yes":
                self.m = imaplib.IMAP4_SSL(self.address, self.port)
            else:
                self.m = imaplib.IMAP4(self.address, self.port)
#        except (imaplib.IMAP4.error, ssl.SSLError), error:
        except Exception, error:
            return False, _("Connection to IMAP server failed, check your configuration")
        try:
            self.m.login(user, passwd)
#        except (imaplib.IMAP4.error, ssl.SSLError), error:
        except Exception, error:
            return False, _("Authentication failed, check your configuration")
            
        return True, None

    def _encodefolder(self, folder):
        if not folder:
            return "INBOX"
        return folder.encode("imap4-utf-7")

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
        return len(self.messages)

    def _parse_folder_name(self, dict, prefix, delimiter, parts):
        if not len(parts):
            return
        path = "%s%s%s" % (prefix, delimiter, parts[0])
        dict[parts[0]] = {"path" : path, "sub" : {}}
        self._parse_folder_name(dict[parts[0]]["sub"], path, delimiter, parts[1:])

    def listfolders(self, topfolder='INBOX', md_folders=[]):
        list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
        (status, data) = self.m.list()
        result = {}
        for mb in data:
            flags, delimiter, name = list_response_pattern.match(mb).groups()
            name = name.strip('"').decode("imap4-utf-7")
            if re.search("\%s" % delimiter, name):
                parts = name.split(".")
                dict = {"path" : parts[0], "sub" : {}}
                self._parse_folder_name(dict["sub"], parts[0], delimiter, parts[1:])
                result[parts[0]] = dict
                continue
            present = False
            for mdf in md_folders:
                if mdf["name"] == name:
                    present = True
                    break
            if not present:
                result[name] = None
        return result

    def msg_unread(self, folder, msgset):
        self.m.select(self._encodefolder(folder), True)
        self.m.store(msgset, "-FLAGS", "\\Seen")

    def msg_read(self, folder, msgset):
        self.m.select(self._encodefolder(folder), True)
        self.m.store(msgset, "+FLAGS", "\\Seen")

    def msgforwarded(self, folder, imapid):
        self.m.select(self._encodefolder(folder), True)
        self.m.store(imapid, "+FLAGS", "$Forwarded")

    def move(self, msgset, oldfolder, newfolder):
        self.m.select(self._encodefolder(oldfolder), True)
        self.m.copy(msgset, newfolder)
        self.m.store(msgset, "+FLAGS", "\\Deleted")

    def empty(self, folder):
        self.m.select(self._encodefolder(folder))
        typ, data = self.m.search(None, 'ALL')
        for num in data[0].split():
            self.m.store(num, "+FLAGS", "\\Deleted")
        self.m.expunge()

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
                msg["imapid"] = "%s/%s" % (folder, imapid)
                if not "\\Seen" in flags:
                    msg["class"] = "unseen"
                if "\\Answered" in flags:
                    msg["img_flags"] = "/static/pics/answered.png"
                tmpdict[imapid] = msg
        for id in submessages:
            result += [tmpdict[id]]
        return result

class ImapListing(EmailListing):
    tpl = "webmail/index.html"
    tbltype = WMtable
    deflocation = "INBOX/"
    defcallback = "wm_updatelisting"
    
    def __init__(self, user, password, **kwargs):
        self.mbc = IMAPconnector(user=user, password=password)
        if kwargs.has_key("pattern"):
            self.parse_search_parameters(kwargs["criteria"],
                                         kwargs["pattern"])
        if kwargs.has_key("reset"):
            self.mbc.criterions = []
        EmailListing.__init__(self, **kwargs)  

    def __parse_folders(self, folders):
        result = []
        for fd in sorted(folders.keys()):
            descr = {"name" : fd}
            if folders[fd] is not None:
                descr["path"] = folders[fd]["path"]
                if folders[fd]["sub"] != {}:
                    descr["icon"] = "subfolders.png"
                    descr["sub"] = self.__parse_folders(folders[fd]["sub"])
            result += [descr]
        return result

    def getfolders(self):
        md_folders = [{"name" : "INBOX", "icon" : "overview.png"},
                      {"name" : 'Drafts'},
                      {"name" : 'Junk'},
                      {"name" : 'Sent'},
                      {"name" : 'Trash', "icon" : "trash.png"}]
        folders = self.mbc.listfolders(md_folders=md_folders)
        md_folders += self.__parse_folders(folders)
        return md_folders

    def parse_search_parameters(self, criterion, pattern):
        def or_criterion(old, c):
            if old == "":
                return c
            return "OR (%s) (%s)" % (old, c)

        criterions = ""
        for c in criterion.split(','):
            if c == "from_addr":
                key = "FROM"
            elif c == "subject":
                key = "SUBJECT"
            else:
                continue
            criterions = or_criterion(criterions, '%s "%s"' % (key, pattern))
        self.mbc.criterions = ["(%s)" % criterions]

class ImapEmail(Email):
    def __init__(self, msg, addrfull=False, **kwargs):
        Email.__init__(self, msg, **kwargs)

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

