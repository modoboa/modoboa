# -*- coding: utf-8 -*-

from datetime import datetime
from django.utils.translation import ugettext as _
from django.db.models import Q
from modoboa.lib import tables, static_url
from modoboa.lib.email_listing import MBconnector, EmailListing
from modoboa.lib.emailutils import *
from models import *

class Qtable(tables.Table):
    tableid = "emails"
    idkey = "mailid"

    type = tables.Column("type", align="center", width="30px",
                         label="<input type='checkbox' name='toggleselect' id='toggleselect' />")
    rstatus = tables.ImgColumn("rstatus", width='25px')
    from_ = tables.Column("from", label=_("From"), limit=30)
    subject = tables.Column("subject", label=_("Subject"), limit=40)
    time = tables.Column("date", label=_("Date"))
    to = tables.Column("to", label=_("To"), sortable=False)

    cols_order = ['type', 'rstatus', 'to', 'from_', 'subject', 'time']

    def parse_date(self, value):
        return datetime.fromtimestamp(value)

class SQLconnector(MBconnector):
    orders = {
        "from" : "mail__from_addr",
        "subject" : "mail__subject",
        "date" : "mail__time_num"
        }
    
    def __init__(self, mail_ids=None, filter=None):
        self.count = None
        self.mail_ids = mail_ids
        self.filter = filter

    def messages_count(self, **kwargs):
        if self.count is None:
            filter = Q(chunk_ind=1)
            if self.mail_ids is not None:
                filter &= Q(mail__in=self.mail_ids)
            if self.filter:
                filter &= self.filter
            self.messages = Quarantine.objects.filter(filter)
            if kwargs.has_key("order"):
                totranslate = kwargs["order"][1:]
                sign = kwargs["order"][:1]
                if sign == " ":
                    sign = ""
                order = sign + self.orders[totranslate]
                self.messages = self.messages.order_by(order)
            self.count = self.messages.count()
        return self.count

    def fetch(self, start=None, stop=None, **kwargs):
        messages = self.messages[start - 1:stop]
        emails = []
        for qm in messages:
            for rcpt in qm.mail.msgrcpt_set.all():
                m = {"from" : qm.mail.from_addr, 
                     "to" : rcpt.rid.email,
                     "subject" : qm.mail.subject,
                     "mailid" : qm.mail_id,
                     "date" : qm.mail.time_num,
                     "type" : qm.mail.content}
                if rcpt.rs == '':
                    m["class"] = "unseen"
                elif rcpt.rs == 'R':
                    m["img_rstatus"] = static_url("pics/release.png")
                emails.append(m)
        return emails

class SQLlisting(EmailListing):
    tpl = "amavis_quarantine/index.html"
    tbltype = Qtable
    deflocation = "listing/"
    defcallback = "updatelisting"
    reset_wm_url = True

    def __init__(self, user, msgs, filter, **kwargs):
        if not user.is_superuser:
            Qtable.cols_order.remove('to')
        self.mbc = SQLconnector(msgs, filter)
        
        super(SQLlisting, self).__init__(**kwargs)

class SQLemail(Email):
    def __init__(self, msg, *args, **kwargs):
        super(SQLemail, self).__init__(msg, *args, **kwargs)
        fields = ["X-Amavis-Alert", "Subject", "From", "To", "Cc", "Date"]
        for f in fields:
            label = f
            if not msg.has_key(f):
                f = f.upper()
                if not msg.has_key(f):
                    self.headers += [{"name" : label, "value" : ""}]
                    continue
            self.headers += [{"name" : label, "value" : msg[f]}]
            try:
                label = re.sub("-", "_", label)
                setattr(self, label, msg[f])
            except:
                pass
