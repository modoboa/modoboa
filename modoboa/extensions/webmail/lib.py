# coding: utf-8
import time
from datetime import datetime, timedelta
import email
from email.utils import parseaddr
from email.header import Header
import lxml
import chardet

from django.core.files.uploadhandler import FileUploadHandler, SkipFile
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings

import os
import re
from modoboa.lib import u2u_decode, tables, parameters
from modoboa.lib.webutils import size2integer
from modoboa.lib.email_listing import EmailListing
from modoboa.extensions.webmail.exceptions import WebmailError
from modoboa.extensions.webmail.imaputils import IMAPconnector, get_imapconnector, BodyStructure
from modoboa.lib.emailutils import EmailAddress, Email


class WMtable(tables.Table):
    tableid = "emails"
    styles = "table-condensed"
    idkey = "imapid"
    select = tables.ImgColumn(
        "select", cssclass="draggable left", width="2%",
        defvalue="%spics/grippy.png" % settings.STATIC_URL,
        header="<input type='checkbox' name='toggleselect' id='toggleselect' />"
        )
    flags = tables.ImgColumn("flags", width="4%")
    withatts = tables.ImgColumn("withatts", width="2%")
    subject = tables.Column("subject", label=ugettext_lazy("Subject"), width="50%", limit=60)
    from_ = tables.Column("from", width="20%", label=ugettext_lazy("From"), limit=30)
    date = tables.Column("date", width="15%", label=ugettext_lazy("Date"))

    cols_order = ["select", "withatts", "flags", "subject", "from_", "date"]

    def parse(self, header, value):
        if value is None:
            return ""
        res = chardet.detect(value)
        try:
            value = getattr(IMAPheader, "parse_%s" % header)(value)
        except AttributeError:
            pass
        if not value or type(value) is unicode or res["encoding"] == "ascii":
            return value
        return value.decode(res["encoding"])

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
    def parse_message_id(value, **kwargs):
        return value.strip('\n')

    @staticmethod
    def parse_subject(value, **kwargs):
        try:
            return u2u_decode.u2u_decode(value)
        except UnicodeDecodeError:
            return value

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
        else:
            self.mbc.criterions = []

        super(ImapListing, self).__init__(**kwargs)
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
    headernames = [
        ('From', True),
        ('To', True),
        ('Cc', True),
        ('Date', True),
        ('Subject', True),
        ]

    def __init__(self, mbox, mailid, request, dformat="DISPLAYMODE", addrfull=False,
                 links=0):
        mformat = parameters.get_user(request.user, "DISPLAYMODE")
        self.dformat = parameters.get_user(request.user, dformat)

        self.headers = []
        self.attachments = {}
        self.imapc = get_imapconnector(request)
        msg = self.imapc.fetchmail(mbox, mailid, readonly=False,
                                   headers=self.headers_as_list)
        self.mbox = mbox
        self.mailid = mailid
        headers = msg['BODY[HEADER.FIELDS (%s)]' % self.headers_as_text]
        fallback_fmt = "html" if self.dformat == "plain" else "plain"

        self.bs = BodyStructure(msg['BODYSTRUCTURE'])
        data = None

        mformat = self.dformat if self.bs.contents.has_key(self.dformat) else fallback_fmt

        if len(self.bs.contents):
            bodyc = u''
            for part in self.bs.contents[mformat]:
                pnum = part['pnum']
                data = self.imapc._cmd("FETCH", mailid, "(BODY.PEEK[%s])" % pnum)
                content = decode_payload(part['encoding'],
                                         data[int(mailid)]['BODY[%s]' % pnum])
                charset = self._find_content_charset(part)
                if charset is not None:
                    try:
                        content = content.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        result = chardet.detect(content)
                        content = content.decode(result['encoding'])
                bodyc += content

            self._fetch_inlines()
            self.body = \
                getattr(self, "viewmail_%s" % mformat)(bodyc, links=links)
        else:
            self.body = None

        self._find_attachments()

        msg = email.message_from_string(headers)
        for hdr in self.headernames:
            label = hdr[0]
            name = hdr[0]
            if not name in msg.keys():
                name = name.upper()
                if not name in msg.keys():
                    continue
            try:
                key = re.sub("-", "_", name).lower()
                value = getattr(IMAPheader, "parse_%s" % key)(msg[name], full=addrfull)
            except AttributeError:
                value = msg[name]
            result = chardet.detect(value)
            if result['encoding'] != 'ascii':
                value = value.decode(result['encoding'])
            if hdr[1]:
                self.headers += [{"name" : label, "value" : value}]
            try:
                label = re.sub("-", "_", label)
                setattr(self, label, value)
            except:
                pass

    @property
    def headers_as_list(self):
        return map(lambda hdr: hdr[0].upper(), self.headernames)

    @property
    def headers_as_text(self):
        return " ".join(map(lambda hdr: hdr[0].upper(), self.headernames))

    def _find_content_charset(self, part):
        for pos, elem in enumerate(part["params"]):
            if elem == "charset":
                return part["params"][pos + 1]
        return None

    def _find_attachments(self):
        for att in self.bs.attachments:
            attname = "part_%s" % att["pnum"]
            params = None
            key = None
            if att.has_key("params") and att["params"] != "NIL":
                params = att["params"]
                key = "name"

            if key is None and \
                    att.has_key("disposition") and len(att["disposition"]) > 1:
                params = att["disposition"][1]
                key = "filename"

            if key and params:
                for pos, value in enumerate(params):
                    if value == key:
                        attname = u2u_decode.u2u_decode(params[pos + 1]).strip("\r\t\n")
                        break
            self.attachments[att["pnum"]] = attname

    def _fetch_inlines(self):
        for cid, params in self.bs.inlines.iteritems():
            if re.search("\.\.", cid):
                continue
            fname = "media/webmail/%s_%s" % (self.mailid, cid)
            path = os.path.join(settings.MODOBOA_DIR, fname)
            params["fname"] = "/%s" % fname
            if os.path.exists(path):
                continue

            pdef, content = self.imapc.fetchpart(self.mailid, self.mbox, params["pnum"])
            fp = open(path, "wb")
            fp.write(decode_payload(params["encoding"], content))
            fp.close()


    def map_cid(self, url):
        import re

        m = re.match(".*cid:(.+)", url)
        if m:
            if self.bs.inlines.has_key(m.group(1)):
                return self.bs.inlines[m.group(1)]["fname"]
        return url

    def render_headers(self, **kwargs):
        from django.template.loader import render_to_string

        res = render_to_string("webmail/headers.html", {
                "headers" : self.headers,
                "folder" : kwargs["folder"], "mail_id" : kwargs["mail_id"],
                "attachments" : self.attachments != {} and self.attachments or None
                })
        return res

class Modifier(ImapEmail):
    def __init__(self, *args, **kwargs):
        super(Modifier, self).__init__(*args, **kwargs)
        getattr(self, "_modify_%s" % self.dformat)()

    def _modify_plain(self):
        self.body = re.sub("</?pre>", "", self.body)

    def _modify_html(self):
        pass


class ReplyModifier(Modifier):
    headernames = ImapEmail.headernames + \
        [("Reply-To", True),
         ("Message-ID", False)]

    def __init__(self, mbox, mailid, request, form,  **kwargs):
        super(ReplyModifier, self).__init__(
            mbox, mailid, request, dformat="EDITOR", **kwargs
            )

        self.textheader = "%s %s" % (self.From, _("wrote:"))

        if hasattr(self, "Message_ID"):
            form.fields["origmsgid"].initial = self.Message_ID
        if not hasattr(self, "Reply_To"):
            form.fields["to"].initial = self.From
        else:
            form.fields["to"].initial = self.Reply_To
        if request.GET.get("all", "0") == "1": # reply-all
            form.fields["cc"].initial = ""
            toparse = self.To.split(",")
            if hasattr(self, 'Cc'):
                toparse += self.Cc.split(",")
            for addr in toparse:
                tmp = EmailAddress(addr)
                if tmp.address and tmp.address == request.user.username:
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
        super(ReplyModifier, self)._modify_plain()
        lines = self.body.split('\n')
        body = ""
        for l in lines:
            if body != "":
                body += "\n"
            body += ">%s" % l
        self.body = body

class ForwardModifier(Modifier):
    def __init__(self, mbox, mailid, request, form, **kwargs):
        super(ForwardModifier, self).__init__(
            mbox, mailid, request, dformat="EDITOR", **kwargs
            )

        self._header()
        form.fields["subject"].initial = "Fwd: %s" % self.Subject

    def __getfunc(self, name):
        return getattr(self, "%s_%s" % (name, self.dformat))

    def _header(self):
        self.textheader = self.__getfunc("_header_begin")() + "\n"
        self.textheader += \
            self.__getfunc("_header_line")(_("Subject"), self.Subject) + "\n"
        self.textheader += \
            self.__getfunc("_header_line")(_("Date"), self.Date) + "\n"
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
        self._sig = ""
        dformat = parameters.get_user(user, "EDITOR")
        content = parameters.get_user(user, "SIGNATURE")
        if len(content):
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

def decode_payload(encoding, payload):
    """Decode the payload according to the given encoding

    Supported encodings: base64, quoted-printable.

    :param encoding: the encoding's name
    :param payload: the value to decode
    :return: a string
    """
    encoding = encoding.lower()
    if encoding == "base64":
        import base64
        return base64.b64decode(payload)
    elif encoding == "quoted-printable":
        import quopri
        return quopri.decodestring(payload)
    return payload

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
        fname = os.path.basename(o.path)
        path = os.path.join(settings.MEDIA_ROOT, "webmail", fname)
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

def set_compose_session(request):
    """Initialize a new "compose" session.

    It is used to keep track of attachments defined with a new
    message. Each new message will be associated with a unique ID (in
    order to avoid conflicts between users).

    :param request: a Request object.
    :return: the new unique ID.
    """
    import uuid
    randid = str(uuid.uuid4()).replace("-", "")
    request.session["compose_mail"] = {"id" : randid, "attachments" : []}
    return randid

def save_attachment(f):
    """Save a new attachment to the filesystem.

    The attachment is not saved using its own name to the
    filesystem. To avoid conflicts, a random name is generated and
    used instead.

    :param f: an uploaded file object (see Django's documentation)
    :return: the new random name
    """
    from tempfile import NamedTemporaryFile

    dstdir = os.path.join(settings.MEDIA_ROOT, "webmail")
    try:
        fp = NamedTemporaryFile(dir=dstdir, delete=False)
    except Exception, e:
        raise WebmailError(str(e))
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return fp.name

def clean_attachments(attlist):
    """Remove all attachments from the filesystem

    :param attlist: a list of 2-uple. Each element must contain the following information :
                    (random name, real name).
    """
    for att in attlist:
        fullpath = os.path.join(settings.MEDIA_ROOT, "webmail", att["tmpname"])
        try:
            os.remove(fullpath)
        except OSError, e:
            pass

def html2plaintext(content):
    """HTML to plain text translation

    :param content: some HTML content
    """
    html = lxml.html.fromstring(content)
    plaintext = ""
    for ch in html.iter():
        p = None
        if ch.text is not None:
            p = ch.text.strip('\r\t\n')
        if ch.tag == "img":
            p = ch.get("alt")
        if p is None:
            continue
        plaintext += p + "\n"

    return plaintext

def get_current_url(request):
    if not request.session.has_key("folder"):
        return ""

    res = "%s?page=%s" % (request.session["folder"], request.session["page"])
    for p in ["criteria", "pattern", "order"]:
        if p in request.session.keys():
            res += "&%s=%s" % (p, request.session[p])
    return res

def create_mail_attachment(attdef):
    """Create the MIME part corresponding to the given attachment.

    Mandatory keys: 'fname', 'tmpname', 'content-type'

    :param attdef: a dictionary containing the attachment definition
    :return: a MIMEBase object
    """
    from email import Encoders
    from email.mime.base import MIMEBase

    maintype, subtype = attdef["content-type"].split("/")
    res = MIMEBase(maintype, subtype)
    fp = open(os.path.join(settings.MEDIA_ROOT, "webmail", attdef["tmpname"]), "rb")
    res.set_payload(fp.read())
    fp.close()
    Encoders.encode_base64(res)
    res.add_header("Content-Disposition", "attachment; filename='%s'" % attdef["fname"])
    return res


def prepare_addresses(addresses, usage="header"):
    """Prepare addresses before using them

    :param list addresses: a list of addresses
    :param string usage: how those addresses are going to be used
    :return: a string or a list depending on usage value
    """
    result = []
    for address in addresses.split(','):
        name, addr = parseaddr(address)
        if name and usage == "header":
            result.append("%s <%s>" % (Header(name, 'utf8').encode(), addr))
        else:
            result.append(addr)
    if usage == "header":
        return ",".join(result)
    return result


def send_mail(request, posturl=None):
    """Email verification and sending.

    If the form does not present any error, a new MIME message is
    constructed. Then, a connection is established with the defined
    SMTP server and the message is finally sent.

    :param request: a Request object
    :param posturl: the url to post the message form to
    :return: a 2-uple (True|False, HttpResponse)
    """
    from email.mime.multipart import MIMEMultipart
    from forms import ComposeMailForm
    from modoboa.lib.webutils import _render_to_string
    from modoboa.auth.lib import get_password

    form = ComposeMailForm(request.POST)
    editormode = parameters.get_user(request.user, "EDITOR")
    if form.is_valid():
        from email.mime.text import MIMEText
        from email.utils import make_msgid, formatdate
        import smtplib

        body = request.POST["id_body"]
        charset = "utf-8"

        if editormode == "html":
            msg = MIMEMultipart(_subtype="related")
            submsg = MIMEMultipart(_subtype="alternative")
            textbody = html2plaintext(body)
            submsg.attach(MIMEText(textbody.encode(charset),
                                   _subtype="plain", _charset=charset))
            body, images = find_images_in_body(body)
            submsg.attach(MIMEText(body.encode(charset), _subtype=editormode,
                                   _charset=charset))
            msg.attach(submsg)
            for img in images:
                msg.attach(img)
        else:
            text = MIMEText(body.encode(charset),
                            _subtype=editormode, _charset=charset)
            if len(request.session["compose_mail"]["attachments"]):
                msg = MIMEMultipart()
                msg.attach(text)
            else:
                msg = text

        for attdef in request.session["compose_mail"]["attachments"]:
            msg.attach(create_mail_attachment(attdef))

        msg["Subject"] = Header(form.cleaned_data["subject"], 'utf8')
        if request.user.first_name != "" or request.user.last_name != "":
            fromaddress = "%s <%s>" % (Header(request.user.fullname, 'utf8').encode(), 
                                       request.user.email)
        else:
            fromaddress = request.user.email
        msg["From"] = fromaddress
        msg["To"] = prepare_addresses(form.cleaned_data["to"])
        msg["Message-ID"] = make_msgid()
        msg["User-Agent"] = "Modoboa"
        msg["Date"] = formatdate(time.time(), True)
        if form.cleaned_data.has_key("origmsgid"):
            msg["References"] = msg["In-Reply-To"] = form.cleaned_data["origmsgid"]
        rcpts = prepare_addresses(form.cleaned_data["to"], "envelope")
        for hdr in ["cc", "cci"]:
            if form.cleaned_data[hdr] != "":
                msg[hdr.capitalize()] = prepare_addresses(form.cleaned_data[hdr])
                rcpts += prepare_addresses(form.cleaned_data[hdr], "envelope")
        try:
            secmode = parameters.get_admin("SMTP_SECURED_MODE")
            if secmode == "ssl":
                s = smtplib.SMTP_SSL(parameters.get_admin("SMTP_SERVER"),
                                     int(parameters.get_admin("SMTP_PORT")))
            else:
                s = smtplib.SMTP(parameters.get_admin("SMTP_SERVER"),
                                 int(parameters.get_admin("SMTP_PORT")))
                if secmode == "starttls":
                    s.starttls()
        except Exception, text:
            raise WebmailError(str(text))

        if parameters.get_admin("SMTP_AUTHENTICATION") == "yes":
            try:
                s.login(request.user.username, get_password(request))
            except smtplib.SMTPAuthenticationError, e:
                raise WebmailError(str(e))
        s.sendmail(request.user.email, rcpts, msg.as_string())
        s.quit()
        sentfolder = parameters.get_user(request.user, "SENT_FOLDER")
        IMAPconnector(user=request.user.username,
                      password=request.session["password"]).push_mail(sentfolder, msg)
        clean_attachments(request.session["compose_mail"]["attachments"])
        del request.session["compose_mail"]
        return True, dict(url=get_current_url(request))

    listing = _render_to_string(request, "webmail/compose.html",
                               {"form" : form, "noerrors" : True,
                                "body" : request.POST["id_body"].strip(),
                                "posturl" : posturl})
    return False, dict(status="ko", listing=listing, editor=editormode)

class AttachmentUploadHandler(FileUploadHandler):
    """
    Simple upload handler to limit the size of the attachments users
    can upload.
    """

    def __init__(self, request=None):
        super(AttachmentUploadHandler, self).__init__(request)
        self.total_upload = 0
        self.toobig = False
        self.maxsize = size2integer(parameters.get_admin("MAX_ATTACHMENT_SIZE"))

    def receive_data_chunk(self, raw_data, start):
        self.total_upload += len(raw_data)
        if self.total_upload >= self.maxsize:
            self.toobig = True
            raise SkipFile()
        return raw_data

    def file_complete(self, file_size):
        return None
