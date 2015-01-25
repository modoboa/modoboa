# coding: utf-8
"""
An email representation based on a database record.
"""

from django.template.loader import render_to_string

from modoboa.lib.emailutils import Email

from .sql_connector import get_connector


class SQLemail(Email):

    """The SQL version of the Email class."""

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
        """Get message's content."""
        import email

        if self._msg is None:
            mail_text = get_connector().get_mail_content(self.mailid)
            self._msg = email.message_from_string(mail_text)
            self._parse(self._msg)
        return self._msg

    def render_headers(self, **kwargs):
        return render_to_string("amavis/mailheaders.html", {
            "qtype": self.qtype, "qreason": self.qreason,
            "headers": self.headers,
        })
