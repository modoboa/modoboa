import email
import re
import smtplib
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, getaddresses, make_msgid

import chardet
import lxml.html
from lxml.html import defs
from lxml.html.clean import Cleaner

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import smart_str, smart_text
from django.utils.html import conditional_escape, escape
from django.utils.translation import ugettext as _

from modoboa.core import models as core_models
from modoboa.lib import u2u_decode
from modoboa.lib.exceptions import InternalError

# used by Email()
_RE_REMOVE_EXTRA_WHITESPACE = re.compile(r"\n\s*\n")
_RE_CID = re.compile(r".*[ ]*cid=\"([^\"]*)\".*", re.I)


class EmailAddress(object):

    def __init__(self, address):
        self.name, self.address = u2u_decode.decode_address(address)
        if self.name:
            self.fulladdress = "{} <{}>".format(self.name, self.address)
        else:
            self.fulladdress = self.address

    def __str__(self):
        return self.fulladdress


class Email(object):

    _basic_headers = (
        "From",
        "To",
        "Cc",
        "Date",
        "Subject",
    )

    _image_mime_types = (
        "image/png",
        "image/gif",
        "image/jpeg",
    )

    def __init__(self, mailid, mformat="plain", dformat="plain", links=False):
        self.contents = {"html": "", "plain": ""}
        self.mailid = mailid
        self.mformat = mformat
        self.dformat = dformat

        if isinstance(links, bool):
            self.links = links
        elif isinstance(links, int):
            # TODO: modoboa-webmail currently sets links == 0 or 1, it needs
            #       updated to use True or False.
            self.links = bool(links)
        elif links == "0":
            raise TypeError("links == \"0\" is not valid, did you mean True or "
                            "False?")
        else:
            raise TypeError("links should be a boolean value")

        self._msg = None
        self._headers = None
        self._body = None
        self._images = {}

        # used by modoboa_webmail.lib.imapemail.ImapEmail
        self.attachments = {}

    @property
    def msg(self):
        if self._msg is None:
            mail_text = self._fetch_message()
            # python 2 expects str (bytes), python 3 expects str (unicode)
            mail_text = smart_str(mail_text, errors="replace")
            self._msg = email.message_from_string(mail_text)

        return self._msg

    @property
    def headers(self):
        if self._headers is None:
            self._headers = []

            # don't break modoboa_webmail.lib.imapemail.ImapEmail, it
            # doesn't have self._msg it loads e-mails (and their headers)
            # from the IMAP server.
            if self._msg is not None:
                for header in self._basic_headers:
                    value = self.get_header(self.msg, header)
                    self._headers.append({
                        "name": header,
                        "value": value
                    })

        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def body(self):
        if self._body is None:
            self._parse(self.msg)
            self._body = getattr(self, "viewmail_%s" % self.dformat)()

        return self._body

    def get_header(self, msg, header):
        # msg parameter to maintain compatibility with
        # modoboa_webmail.lib.imapemail.ImapEmail
        if header in msg:
            decoded_values = []
            for value, encoding in email.header.decode_header(msg[header]):
                if not len(value):
                    continue
                if encoding:
                    value = smart_text(value, encoding=encoding)
                elif isinstance(value, bytes):
                    # SMTPUTF8 fallback (most of the time)
                    # Address contains non ASCII chars but is not RFC2047
                    # encoded...
                    encoding = chardet.detect(value)
                    try:
                        value = value.decode(encoding["encoding"], "replace")
                    except (TypeError, UnicodeDecodeError) as exc:
                        raise InternalError(
                            _("unable to determine encoding of string")
                        ) from exc
                decoded_values.append(value)
            return "".join(decoded_values)
        return ""

    def _fetch_message(self):
        raise NotImplementedError()

    def _parse(self, msg, level=0):
        """Recursive email parser

        A message structure can be complex. To correctly handle
        unknown MIME types, a simple rule is applied : if I don't know
        how to display a specific part, it becomes an attachment! If
        no name is specified for an attachment, the part number
        described in the RFC 3501 (which retrieves BODY sections) is
        used to build a file name (like part_1.1).

        :param msg: message (or part) to parse
        :param level: current part number
        """
        content_type = msg.get_content_maintype()
        is_attachment = "attachment" in msg.get("Content-Disposition", "")

        if content_type == "text" and not is_attachment:
            self._parse_text(msg, level)
        elif content_type == "multipart" and not is_attachment:
            self._parse_multipart(msg, level)
        else:
            self._parse_inline_image(msg, level)

        if self.contents["plain"]:
            self.contents["plain"] = self._post_process_plain(
                self.contents["plain"])
        if self.contents["html"]:
            self.contents["html"] = self._post_process_html(
                self.contents["html"])

    def _parse_text(self, msg, level=0):
        content_type = msg.get_content_subtype()

        if content_type in ["plain", "html"]:
            encoding = msg.get_content_charset() or "utf-8"
            mail_text_bytes = msg.get_payload(decode=True)
            mail_text = decode(mail_text_bytes, encoding)
            self.contents[content_type] += mail_text

    def _parse_multipart(self, msg, level=0):
        level += 1
        for part in msg.walk():
            content_type = part.get_content_maintype()
            if content_type == "text":
                self._parse_text(part, level=level)
            else:
                # I'm  a dumb mail parser and treat all non-text parts as
                # attachments
                self._parse_inline_image(part, level=level)

    def _parse_inline_image(self, msg, level=0):
        content_type = msg.get_content_type()
        cid = None
        if "Content-ID" in msg:
            cid = msg["Content-ID"]
            if cid.startswith("<") and cid.endswith(">"):
                cid = cid[1:-1]
        else:
            matches = _RE_CID.match(msg["Content-Type"])
            if matches is not None:
                cid = matches.group(1)
        transfer_encoding = msg["Content-Transfer-Encoding"]
        if content_type not in self._image_mime_types or cid is None:
            # I'm a dumb mail parser and I don't care ;p
            return
        if transfer_encoding != "base64":
            # I don't deal with non base64 encoded images
            return
        if cid in self._images:
            # Duplicate Content-ID
            return

        self._images[cid] = "data:%s;base64,%s" % (
            content_type, "".join(msg.get_payload().splitlines(False)))

    def _post_process_plain(self, content):
        mail_text = (
            _RE_REMOVE_EXTRA_WHITESPACE.sub("\n\n", content).strip()
        )
        mail_text = escape(mail_text)
        return smart_text(mail_text)

    def _post_process_html(self, content):
        html = lxml.html.fromstring(content)
        if self.links:
            html.rewrite_links(self._map_cid)

            for link in html.iterlinks():
                link[0].set("target", "_blank")
        else:
            html.rewrite_links(lambda x: None)
        safe_attrs = list(defs.safe_attrs) + ["class", "style"]
        cleaner = Cleaner(
            scripts=True,
            javascript=True,
            links=True,
            page_structure=True,
            embedded=True,
            frames=True,
            add_nofollow=True,
            safe_attrs=safe_attrs
        )
        mail_text = lxml.html.tostring(cleaner.clean_html(html))
        return smart_text(mail_text)

    def _map_cid(self, url):
        if url.startswith("cid:"):
            cid = url[4:]
            if cid in self._images:
                url = self._images[cid]

        return url

    def viewmail_plain(self, contents=None, **kwargs):
        # contents and **kwargs parameters to maintain compatibility with
        # modoboa_webmail.lib.imapemail.ImapEmail
        if contents is None:
            contents = self.contents["plain"]
        else:
            contents = conditional_escape(contents)
        return "<pre>%s</pre>" % contents

    def viewmail_html(self, contents=None, **kwargs):
        # contents and **kwargs parameters to maintain compatibility with
        # modoboa_webmail.lib.imapemail.ImapEmail
        if contents is None:
            contents = self.contents["html"]
        return contents

    def render_headers(self, **kwargs):
        context = {
            "headers": self.headers,
        }
        return render_to_string("common/mailheaders.html", context)


def split_address(address):
    """Split an e-mail address into local part and domain."""
    assert isinstance(address, str),\
        "address should be of type str"
    if "@" not in address:
        local_part = address
        domain = None
    else:
        local_part, domain = address.rsplit("@", 1)
    return (local_part, domain)


def split_local_part(local_part, delimiter=None):
    """Split a local part into local part and extension."""
    assert isinstance(local_part, str),\
        "local_part should be of type str"
    assert isinstance(delimiter, str) or delimiter is None,\
        "delimiter should be of type str"
    extension = None
    if local_part.lower() in ["mailer-daemon", "double-bounce"]:
        # never split these special addresses
        pass
    elif (
        delimiter == "-" and
         (local_part.startswith("owner-") or
          local_part.endswith("-request"))
    ):
        # don't split owner-* or *-request if - is the delimiter, they are
        # special addresses used by mail lists.
        pass
    elif (
        delimiter and
        delimiter in local_part and
        local_part[0] != delimiter and
        local_part[-1] != delimiter
    ):
        local_part, extension = local_part.split(delimiter, 1)

    return (local_part, extension)


def split_mailbox(mailbox, return_extension=False):
    """Try to split an address into parts (local part and domain name).

    If return_extension is True, we also look for an address extension
    (something foo+bar).

    :return: a tuple (local part, domain<, extension>)

    """
    local_part, domain = split_address(mailbox)
    if not return_extension:
        return (local_part, domain)
    local_part, extension = split_local_part(local_part, delimiter="+")
    return (local_part, domain, extension)


def decode(value_bytes, encoding, append_to_error=""):
    """Try to decode the given string."""
    assert isinstance(value_bytes, bytes),\
        "value_bytes should be of type bytes"
    if len(value_bytes) == 0:
        # short circuit for empty strings
        return ""
    try:
        value = value_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        encoding = chardet.detect(value_bytes)
        try:
            value = value_bytes.decode(
                encoding["encoding"], "replace"
            )
        except (TypeError, UnicodeDecodeError) as exc:
            raise InternalError(
                _("unable to determine encoding of string") +
                append_to_error
            ) from exc
    return value


def prepare_addresses(addresses, usage="header"):
    """Prepare addresses before using them

    :param list addresses: a list of addresses
    :param string usage: how those addresses are going to be used
    :return: a string or a list depending on usage value
    """
    result = []
    if isinstance(addresses, str):
        addresses = [addresses]
    for name, address in getaddresses(addresses):
        if not address:
            continue
        if name and usage == "header":
            result.append(formataddr((name, address)))
        else:
            result.append(address)
    if usage == "header":
        return ",".join(result)
    return result


def set_email_headers(msg, subject, sender, rcpt):
    """Set mandatory headers.

    Subject, From, To, Message-ID, User-Agent, Date
    """
    import pkg_resources

    msg["Subject"] = Header(subject, "utf8")
    msg["From"] = sender
    msg["To"] = prepare_addresses(rcpt)
    msg["Message-ID"] = make_msgid()
    msg["User-Agent"] = "Modoboa %s" % \
        (pkg_resources.get_distribution("modoboa").version)
    msg["Date"] = formatdate(time.time(), True)


def _sendmail(sender, rcpt, msgstring, server="localhost", port=25):
    """Message sending

    Return a tuple (True, None) on success, (False, error message)
    otherwise.

    :param sender: sender address
    :param rcpt: recipient address
    :param msgstring: the message structure (must be a string)
    :param server: the sending server's address
    :param port: the listening port
    :return: tuple
    """
    try:
        s = smtplib.SMTP(server, port)
        s.sendmail(sender, [rcpt], msgstring)
        s.quit()
    except smtplib.SMTPException as e:
        return False, "SMTP error: %s" % str(e)
    return True, None


def sendmail_simple(
        sender, rcpt, subject="Sample message", content="", **kwargs):
    """Simple way to send a text message

    Send a text/plain message with basic headers (msg-id, date).

    Return a tuple (True, None) on success, (False, error message)
    otherwise.

    :param sender: sender address
    :param rcpt: recipient address
    :param subject: message's subject
    :param content: message's content
    :return: tuple
    """
    msg = MIMEText(content, _charset="utf-8")
    set_email_headers(msg, subject, sender, rcpt)
    return _sendmail(sender, rcpt, msg.as_string(), **kwargs)


def sendmail_fromfile(sender, rcpt, fname):
    """Send a message contained within a file

    The given file name must represent a valid message structure. It
    must not include the From: and To: headers, they are automatically
    added by the function.

    :param sender: sender address
    :param rcpt: recipient address
    :param fname: the name of the file containing the message
    :return: a tuple
    """
    try:
        fp = open(fname)
    except IOError as e:
        return False, str(e)

    content = """From: %s
To: %s
""" % (sender, rcpt)
    content += fp.read()
    fp.close()

    return _sendmail(sender, rcpt, content)


def send_notification(recipient, subject, tpl, sender=None, **kwargs):
    """Send notification by email."""
    if not sender:
        local_config = (
            core_models.LocalConfig.objects.select_related("site").first())
        sender = local_config.parameters.get_value("sender_address")
    content = render_to_string(tpl, kwargs)
    msg = EmailMessage(
        subject, content.strip(), sender, [recipient],
    )
    msg.send()
