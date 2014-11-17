"""
Set of classes to manipulate/display emails inside the webmail.
"""
import os
import re
import email

import chardet
from rfc6266 import parse_headers

from django.conf import settings
from django.utils.translation import ugettext as _

from modoboa.lib import parameters, u2u_decode
from modoboa.lib.emailutils import Email, EmailAddress
from .imaputils import (
    get_imapconnector, BodyStructure
)
from .utils import decode_payload


class ImapEmail(Email):

    """
    A class to represent an email fetched from an IMAP server.
    """

    headernames = [
        ('From', True),
        ('To', True),
        ('Cc', True),
        ('Date', True),
        ('Subject', True),
    ]

    def __init__(self, request, addrfull, *args, **kwargs):
        super(ImapEmail, self).__init__(*args, **kwargs)
        self.request = request
        self.addrfull = addrfull
        self.imapc = get_imapconnector(request)
        self.mbox, self.mailid = self.mailid.split(":")

        headers = self.msg['BODY[HEADER.FIELDS (%s)]' % self.headers_as_text]
        msg = email.message_from_string(headers)
        for hdr in self.headernames:
            label = hdr[0]
            hdrvalue = self.get_header(msg, label)
            if not hdrvalue:
                continue
            if hdr[1]:
                self.headers += [{"name": label, "value": hdrvalue}]
            label = re.sub("-", "_", label)
            setattr(self, label, hdrvalue)

    def get_header(self, msg, hdrname):
        """Look for a particular header.

        We also try to decode the default value.
        """
        from . import imapheader

        hdrvalue = super(ImapEmail, self).get_header(msg, hdrname)
        if not hdrvalue:
            return ""
        try:
            key = re.sub("-", "_", hdrname).lower()
            hdrvalue = getattr(imapheader, "parse_%s" % key)(
                hdrvalue, full=self.addrfull
            )
        except AttributeError:
            pass
        return hdrvalue

    @property
    def msg(self):
        """
        """
        if self._msg is None:
            self._msg = self.imapc.fetchmail(
                self.mbox, self.mailid, readonly=False,
                headers=self.headers_as_list
            )
            self.bs = BodyStructure(self._msg['BODYSTRUCTURE'])
            self._find_attachments()
            if not self.dformat in ["plain", "html"]:
                self.dformat = parameters.get_user(
                    self.request.user, self.dformat
                )
            fallback_fmt = "html" if self.dformat == "plain" else "plain"
            self.mformat = self.dformat \
                if self.dformat in self.bs.contents else fallback_fmt
        return self._msg

    @property
    def headers_as_list(self):
        return [hdr[0].upper() for hdr in self.headernames]

    @property
    def headers_as_text(self):
        return " ".join(self.headers_as_list)

    @property
    def body(self):
        """Load email's body.

        This operation has to be made "on demand" because it requires
        a communication with the IMAP server.

        """
        if self._body is None and self.bs.contents:
            bodyc = u''
            for part in self.bs.contents[self.mformat]:
                pnum = part['pnum']
                data = self.imapc._cmd(
                    "FETCH", self.mailid, "(BODY.PEEK[%s])" % pnum
                )
                content = decode_payload(
                    part['encoding'], data[int(self.mailid)]['BODY[%s]' % pnum]
                )
                charset = self._find_content_charset(part)
                if charset is not None:
                    try:
                        content = content.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        result = chardet.detect(content)
                        content = content.decode(result['encoding'])
                bodyc += content
            self._fetch_inlines()
            self._body = getattr(self, "viewmail_%s" % self.mformat)(
                bodyc, links=self.links
            )
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    def _find_content_charset(self, part):
        for pos, elem in enumerate(part["params"]):
            if elem == "charset":
                return part["params"][pos + 1]
        return None

    def _find_attachments(self):
        """Retrieve attachments from the parsed body structure.

        We try to find and decode a file name for each attachment. If
        we failed, a generic name will be used (ie. part_1, part_2, ...).
        """
        for att in self.bs.attachments:
            attname = "part_%s" % att["pnum"]
            if "params" in att and att["params"] != "NIL":
                attname = u2u_decode.u2u_decode(att["params"][1]) \
                    .strip("\r\t\n")
            elif "disposition" in att and len(att["disposition"]) > 1:
                for pos, value in enumerate(att["disposition"][1]):
                    if not value.startswith("filename"):
                        continue
                    header = "%s; %s=%s" \
                        % (att['disposition'][0],
                           value,
                           att["disposition"][1][pos + 1].strip("\r\t\n"))
                    attname = parse_headers(header).filename_unsafe
                    if attname is None:
                        attname = u2u_decode.u2u_decode(
                            att["disposition"][1][pos + 1]
                        ).strip("\r\t\n")
                    break
            self.attachments[att["pnum"]] = attname

    def _fetch_inlines(self):
        for cid, params in self.bs.inlines.iteritems():
            if re.search(r"\.\.", cid):
                continue
            fname = "webmail/%s_%s" % (self.mailid, cid)
            path = os.path.join(settings.MEDIA_ROOT, fname)
            params["fname"] = os.path.join(settings.MEDIA_URL, fname)
            if os.path.exists(path):
                continue

            pdef, content = self.imapc.fetchpart(
                self.mailid, self.mbox, params["pnum"]
            )
            with open(path, "wb") as fpo:
                fpo.write(decode_payload(params["encoding"], content))

    def map_cid(self, url):
        m = re.match(".*cid:(.+)", url)
        if m:
            if m.group(1) in self.bs.inlines:
                return self.bs.inlines[m.group(1)]["fname"]
        return url

    def render_headers(self, **kwargs):
        from django.template.loader import render_to_string

        res = render_to_string("webmail/headers.html", {
            "headers": self.headers,
            "folder": kwargs["folder"], "mail_id": kwargs["mail_id"],
            "attachments": self.attachments != {} and self.attachments or None
        })
        return res

    def fetch_attachment(self, pnum):
        """Fetch an attachment from the IMAP server.
        """
        return self.imapc.fetchpart(self.mailid, self.mbox, pnum)


class Modifier(ImapEmail):

    """Message modifier."""

    def __init__(self, form, *args, **kwargs):
        kwargs["dformat"] = "EDITOR"
        super(Modifier, self).__init__(*args, **kwargs)
        self.form = form
        getattr(self, "_modify_%s" % self.dformat)()

    def _modify_plain(self):
        self.body = re.sub("</?pre>", "", self.body)

    def _modify_html(self):
        if self.dformat == "html" and self.mformat != self.dformat:
            self.body = re.sub("</?pre>", "", self.body)
            self.body = re.sub("\n", "<br>", self.body)

    @property
    def subject(self):
        """Just a shortcut to return a subject in any case."""
        return self.Subject if hasattr(self, "Subject") else ""


class ReplyModifier(Modifier):

    """Modify a message to reply to it."""

    headernames = ImapEmail.headernames + \
        [("Reply-To", True),
         ("Message-ID", False)]

    def __init__(self, *args, **kwargs):
        super(ReplyModifier, self).__init__(*args, **kwargs)

        self.textheader = "%s %s" % (self.From, _("wrote:"))
        if hasattr(self, "Message_ID"):
            self.form.fields["origmsgid"].initial = self.Message_ID
        if not hasattr(self, "Reply_To"):
            self.form.fields["to"].initial = self.From
        else:
            self.form.fields["to"].initial = self.Reply_To
        if self.request.GET.get("all", "0") == "1":  # reply-all
            self.form.fields["cc"].initial = ""
            toparse = self.To.split(",")
            if hasattr(self, 'Cc'):
                toparse += self.Cc.split(",")
            for addr in toparse:
                tmp = EmailAddress(addr)
                if tmp.address and tmp.address == self.request.user.username:
                    continue
                if self.form.fields["cc"].initial != "":
                    self.form.fields["cc"].initial += ", "
                self.form.fields["cc"].initial += tmp.fulladdress
        m = re.match(r"re\s*:\s*.+", self.subject.lower())
        if m:
            self.form.fields["subject"].initial = self.subject
        else:
            self.form.fields["subject"].initial = "Re: %s" % self.subject

    def _modify_plain(self):
        super(ReplyModifier, self)._modify_plain()
        lines = self.body.split('\n')
        body = ""
        for l in lines:
            if body != "":
                body += "\n"
            body += ">%s" % l
        self.body = body


class ForwardModifier(Modifier):

    """
    Modify a message so it can be forwarded.
    """

    def __init__(self, *args, **kwargs):
        super(ForwardModifier, self).__init__(*args, **kwargs)
        self._header()
        self.form.fields["subject"].initial = "Fwd: %s" % self.subject

    def __getfunc(self, name):
        return getattr(self, "%s_%s" % (name, self.dformat))

    def _header(self):
        self.textheader = self.__getfunc("_header_begin")() + "\n"
        self.textheader += \
            self.__getfunc("_header_line")(_("Subject"), self.subject)
        self.textheader += \
            self.__getfunc("_header_line")(_("Date"), self.Date)
        for hdr in ["From", "To", "Reply-To"]:
            try:
                key = re.sub("-", "_", hdr)
                value = getattr(self, key)
                self.textheader += \
                    self.__getfunc("_header_line")(_(hdr), value)
            except AttributeError:
                pass
        self.textheader += self.__getfunc("_header_end")()

    def _header_begin_plain(self):
        return "----- %s -----" % _("Original message")

    def _header_begin_html(self):
        return  "----- %s -----" % _("Original message")

    def _header_line_plain(self, key, value):
        return "%s: %s\n" % (key, value)

    def _header_line_html(self, key, value):
        return "<p>%s: %s</p>" % (key, value)

    def _header_end_plain(self):
        return "\n"

    def _header_end_html(self):
        return ""
