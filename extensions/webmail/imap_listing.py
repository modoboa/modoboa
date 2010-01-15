# -*- coding: utf-8 -*-

import re
import time
from datetime import datetime, timedelta
from email.header import decode_header
import email.utils
from django.utils.translation import ugettext as _
from mailng.lib import decode, tables, imap_utf7
from mailng.lib.email_listing import MBconnector, EmailListing
from mailng.lib import tables, imap_utf7, parameters

class WMtable(tables.Table):
    idkey = "imapid"
    selection = tables.SelectionColumn("selection", first=True)
    subject = tables.Column("subject", label=_("Subject"))
    from_ = tables.Column("from", label=_("From"))
    date = tables.Column("date", label=_("Date"))
    from_exp = re.compile("([^<]+)<([^>]+)>")
    name_exp = re.compile("\"(.+)\"")

    def parse_from(self, value):
        m = self.from_exp.match(value)
        if m:
            name = m.group(1)
            name = name.strip()
            m2 = self.name_exp.match(name)
            if m2:
                return m2.group(1)
            return m.group(1)
        return value

    def parse_date(self, value):
        ndate = datetime(*(email.utils.parsedate_tz(value))[:7])
        now = datetime.now()
        if now - ndate > timedelta(7):
            return ndate.strftime("%d.%m.%Y %H:%M")
        return ndate.strftime("%a %H:%M")

    def parse_subject(self, value):
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
        return int(data[0])

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

    def fetch(self, start=None, stop=None, folder=None, all=False):
        if not start and not stop:
            return []
        result = []
        self.m.select(self._encodefolder(folder))
        if start and stop:
            range = "%d:%d" % (start, stop)
        else:
            range = start
        if not all:
            query = '(BODY[HEADER.FIELDS (DATE FROM TO SUBJECT)])'
        else:
            query = '(RFC822)'
        typ, data = self.m.fetch(range, query)
        imapid = int(start)
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])
                msg["imapid"] = imapid
                result += [msg]
                imapid = imapid + 1
        return result

class ImapListing(EmailListing):
    tpl = "webmail/index.html"
    
    def __init__(self, user, password, **kwargs):
        self.mbc = IMAPconnector(parameters.get("webmail", "SERVER_ADDRESS"), 143)
        status, text = self.mbc.login(user, password)
        if not status:
            print "Login error: %s" % text
        EmailListing.__init__(self, **kwargs)

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

    def fetch(self, id_start, id_stop):
        return WMtable(self.mbc.fetch(start=id_start, stop=id_stop, 
                                      folder=self.folder))
