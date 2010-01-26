# -*- coding: utf-8 -*-

import re
import time
import imaplib
from datetime import datetime, timedelta
from email.header import decode_header
import email.utils
from django.utils.translation import ugettext as _
from mailng.lib import decode, tables, imap_utf7
from mailng.lib.email_listing import MBconnector, EmailListing
from mailng.lib import tables, imap_utf7, parameters


class WMtable(tables.Table):
    tableid = "emails"
    idkey = "imapid"
    selection = tables.SelectionColumn("selection", width="20px", first=True)
    _1_flags = tables.ImgColumn("flags", width="40px")
    _2_subject = tables.Column("subject", width="50%", label=_("Subject"))
    _3_from_ = tables.Column("from", width="20%", label=_("From"))
    _4_date = tables.Column("date", width="20%", label=_("Date"))


    def parse(self, header, value):
        try:
            return getattr(IMAPheader, "parse_%s" % header)(value)
        except AttributeError:
            return value

class IMAPheader(object):
    addr_exp = re.compile("([^<\(]+)<|\(([^>\)]+)>|\)")
    name_exp = re.compile("\"(.+)\"")

    @staticmethod
    def parse_address(value):
        m = IMAPheader.addr_exp.match(value)
        if m:
            name = m.group(1)
            name = name.strip()
            m2 = IMAPheader.name_exp.match(name)
            if m2:
                return IMAPheader.parse_subject(m2.group(1))
            return IMAPheader.parse_subject(name)
        return value

    @staticmethod
    def parse_address_list(values):
        lst = values.split(",")
        result = ""
        for addr in lst:
            if result != "":
                result += ", "
            result += IMAPheader.parse_address(addr)
        return result

    @staticmethod
    def parse_from(value):
        return IMAPheader.parse_address(value)

    @staticmethod
    def parse_to(value):
        return IMAPheader.parse_address_list(value)

    @staticmethod
    def parse_cc(value):
        return IMAPheader.parse_address_list(value)

    @staticmethod
    def parse_date(value):
        ndate = datetime(*(email.utils.parsedate_tz(value))[:7])
        now = datetime.now()
        if now - ndate > timedelta(7):
            return ndate.strftime("%d.%m.%Y %H:%M")
        return ndate.strftime("%a %H:%M")

    @staticmethod
    def parse_subject(value):
        res = ""
        dcd = decode_header(value)
        for part in dcd:
            if res != "":
                res += " "
            res += part[0].strip(" ")
        return decode(res)
    
class IMAPconnector(MBconnector):
    def login(self, user, passwd):
        import imaplib

        try:
            self.m = imaplib.IMAP4_SSL(self.address)
            self.m.login(user, passwd)
        except imaplib.IMAP4.error, test:
            return False, test
        return True, None

    def _encodefolder(self, folder):
        if not folder:
            return "INBOX"
        return folder.encode("imap4-utf-7")

    def messages_count(self, folder=None):
        (status, data) = self.m.select(self._encodefolder(folder))
        (status, data) = self.m.sort("(REVERSE DATE)", "UTF-8", "(NOT DELETED)")
        self.messages = data[0].split()
        return len(self.messages)

    def listfolders(self, topfolder='INBOX', md_folders=[]):
        (status, data) = self.m.list()
        result = []
        for mb in data:
            attrs, truc, name = mb.split()
            name = name.strip('"').decode("imap4-utf-7")
            present = False
            for mdf in md_folders:
                if mdf["name"] == name:
                    present = True
                    break
            if not present:
                result += [name]
        return sorted(result)

    def msgseen(self, imapid):
        folder, id = imapid.split("/")
        self.m.store(id, "+FLAGS", "\\Seen")

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
    
    def __init__(self, user, password, baseurl=None, **kwargs):
        self.mbc = IMAPconnector(parameters.get("webmail", "IMAP_SERVER"), 143)
        status, text = self.mbc.login(user, password)
        if not status:
            print "Login error: %s" % text
        EmailListing.__init__(self, **kwargs)
        if baseurl:
            self.paginator.baseurl = baseurl

    def getfolders(self):
        md_folders = [{"name" : "INBOX", "icon" : "overview.png"},
                      {"name" : 'Drafts'},
                      {"name" : 'Junk'},
                      {"name" : 'Sent'},
                      {"name" : 'Trash', "icon" : "trash.png"}]
        folders = self.mbc.listfolders(md_folders=md_folders)
        for fd in folders:
            md_folders += [{"name" : fd}]
        return md_folders
