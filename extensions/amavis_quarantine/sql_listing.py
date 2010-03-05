# -*- coding: utf-8 -*-

from datetime import datetime
from django.utils.translation import ugettext as _
from mailng.lib import tables, db
from mailng.lib.email_listing import MBconnector, EmailListing

class Qtable(tables.Table):
    idkey = "mailid"
    selection = tables.SelectionColumn("selection", first=True)
    type = tables.Column("type", label=_("Type"))
    from_ = tables.Column("from", label=_("From"))
    subject = tables.Column("subject", label=_("Subject"))
    time = tables.Column("date", label=_("Date"))

    def parse_date(self, value):
        return datetime.fromtimestamp(value)

    def parse(self, header, value):
        try:
            return getattr(self, "parse_%s" % header)(value)
        except AttributeError:
            return value

class SQLconnector(MBconnector):
    def __init__(self, filter=None):
        self.conn = db.getconnection("amavis_quarantine")
        self.filter = ""
        if filter:
            for a in filter:
                if not a:
                    continue
                if a[0] == "&":
                    self.filter += " AND "
                else:
                    self.filter += " OR "
                self.filter += a[1:]
        query = self._get_query()
        status, cursor = db.execute(self.conn, """
SELECT count(quarantine.mail_id) AS total
%s
""" % query)
        if not status:
            print cursor
            self.count = 0
        else:
            self.count = int(cursor.fetchone()[0])

    def _get_query(self):
        return """
FROM quarantine, maddr, msgrcpt, msgs
WHERE quarantine.mail_id=msgrcpt.mail_id
AND msgrcpt.rid=maddr.id
AND msgrcpt.mail_id=msgs.mail_id
AND quarantine.chunk_ind=1
%s
ORDER BY msgs.time_num DESC
""" % self.filter

    def messages_count(self, **kwargs):
        return self.count

    def fetch(self, start=None, stop=None, **kwargs):
        query = self._get_query()
        status, cursor = db.execute(self.conn, """
SELECT msgs.from_addr, maddr.email, msgs.subject, msgs.content, quarantine.mail_id,
       msgs.time_num, msgs.content
%s
LIMIT %d,%d
""" % (query, start - 1, stop - 1))
        if not status:
            print cursor
            return []
        emails = []
        rows = cursor.fetchall()
        for row in rows:
            emails.append({"from" : row[0], "to" : row[1], 
                           "subject" : row[2], "content" : row[3],
                           "mailid" : row[4], "date" : row[5],
                           "type" : row[6]})
        return emails

class SQLlisting(EmailListing):
    tpl = "amavis_quarantine/index.html"
    tbltype = Qtable

    def __init__(self, filter, **kwargs):
        self.mbc = SQLconnector(filter)
        EmailListing.__init__(self, **kwargs)
