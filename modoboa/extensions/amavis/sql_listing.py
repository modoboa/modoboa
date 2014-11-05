# coding: utf-8
from datetime import datetime

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy

from modoboa.lib import tables
from modoboa.lib.email_listing import EmailListing
from modoboa.lib.emailutils import Email

from .sql_connector import get_connector


class Qtable(tables.Table):
    tableid = "emails"
    styles = "table-condensed"
    idkey = "mailid"

    selection = tables.SelectionColumn(
        "selection", safe=True, width='5px', header=None, sortable=False
    )
    type = tables.Column(
        "type", align="center", width="30px", sort_order="type", safe=True
    )
    rstatus = tables.ImgColumn(
        "rstatus", width='25px', sortable=False, bootstrap=True
    )
    score = tables.Column(
        "score", label=ugettext_lazy("Score"), limit=6,
        sort_order="score", cssclass="openable"
    )
    to = tables.Column(
        "to", label=ugettext_lazy("To"), sort_order="to", cssclass="openable"
    )
    from_ = tables.Column(
        "from", label=ugettext_lazy("From"), limit=30,
        sort_order="from", cssclass="openable"
    )
    subject = tables.Column(
        "subject", label=ugettext_lazy("Subject"), limit=40,
        sort_order="subject", cssclass="openable"
    )
    time = tables.Column(
        "date", label=ugettext_lazy("Date"), sort_order="date",
        cssclass="openable"
    )

    cols_order = [
        'selection', 'type', 'rstatus', 'score', 'to', 'from_', 'subject',
        'time'
    ]

    def parse_type(self, value):
        if value in ['S', 'V']:
            color = 'important'
        elif value == 'C':
            color = 'success'
        else:
            color = 'warning'
        return '<span class="label label-%s">%s</span>' % (color, value)

    def parse_date(self, value):
        return datetime.fromtimestamp(value)


class SQLlisting(EmailListing):
    tpl = "amavis/index.html"
    tbltype = Qtable
    deflocation = "listing/"
    defcallback = "updatelisting"
    reset_wm_url = True

    def __init__(self, user, **kwargs):
        self.mbc = get_connector(user=user, navparams=kwargs["navparams"])
        super(SQLlisting, self).__init__(**kwargs)
        self.show_listing_headers = True


class SQLemail(Email):
    def __init__(self, *args, **kwargs):
        super(SQLemail, self).__init__(*args, **kwargs)
        fields = ["From", "To", "Cc", "Date", "Subject"]
        for f in fields:
            label = f
            self.headers += [
                {"name": label, "value": self.get_header(self.msg, f)}
            ]
            setattr(self, label, self.msg[f])
        qreason = self.get_header(self.msg, "X-Amavis-Alert")
        self.qtype = ""
        self.qreason = ""
        if qreason != "":
            if ',' in qreason:
                self.qtype, self.qreason = qreason.split(',', 1)
            elif qreason.startswith("BAD HEADER SECTION "):
                # Workaround for amavis <= 2.8.0 :p
                self.qtype = "BAD HEADER SECTION"
                self.qreason = qreason[19:]

    @property
    def msg(self):
        """
        """
        import email

        if self._msg is None:
            qmails = get_connector().get_mail_content(self.mailid)
            self._msg = email.message_from_string(
                "".join([qm.mail_text for qm in qmails])
            )
            self._parse(self._msg)
        return self._msg

    def render_headers(self, **kwargs):
        return render_to_string("amavis/mailheaders.html", {
            "qtype": self.qtype, "qreason": self.qreason,
            "headers": self.headers,
        })
