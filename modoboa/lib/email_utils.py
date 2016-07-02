# coding: utf-8

import re
import smtplib
import time
from email.header import Header, decode_header
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate, parseaddr

from django.conf import settings
from django.template.loader import render_to_string

from modoboa.lib import u2u_decode


class EmailAddress(object):

    def __init__(self, address):
        self.fulladdress = u2u_decode.u2u_decode(address).strip("\r\t\n")
        (self.name, self.address) = parseaddr(self.fulladdress)
        if self.name == "":
            self.fulladdress = self.address

    def __str__(self):
        return self.fulladdress


class Email(object):

    def __init__(self, mailid, mformat="plain", dformat="plain", links=0):
        self.attached_map = {}
        self.contents = {"html": "", "plain": ""}
        self.headers = []
        self.attachments = {}
        self.mailid = mailid
        self.mformat = mformat
        self.dformat = dformat
        self.links = links
        self._msg = None
        self._body = None

    @property
    def msg(self):
        """Return an email.message object.
        """
        raise NotImplementedError

    @property
    def body(self):
        """Return email's body."""
        if self._body is None:
            self._body = (
                getattr(self, "viewmail_%s" % self.mformat)
                (self.contents[self.mformat], links=self.links)
            )
        return self._body

    def get_header(self, msg, hdrname):
        """Look for a particular header.

        :param string hdrname: header name
        :return: header avalue
        """
        for name in [hdrname, hdrname.upper()]:
            if name in msg:
                return msg[name]
        return ""

    def _parse_default(self, msg, level):
        """Default parser

        All parts handled by this parser will be consireded as
        attachments.
        """
        fname = msg.get_filename()
        if fname is not None:
            if type(fname) is unicode:
                fname = fname.encode("utf-8")
            decoded = decode_header(fname)
            value = (
                decoded[0][0] if decoded[0][1] is None
                else unicode(decoded[0][0], decoded[0][1])
            )
        else:
            value = "part_%s" % level
        self.attachments[level] = value

    def _parse_text(self, msg, level):
        """Displayable content parser

        text, html, calendar, etc. All those contents can be displayed
        inside a navigator.
        """
        if msg.get_content_subtype() not in ["plain", "html"]:
            self._parse_default(msg, level)
            target = "plain"
        else:
            target = msg.get_content_subtype()
        self.contents[target] += decode(msg.get_payload(decode=True),
                                        charset=msg.get_content_charset())

    def _parse_image(self, msg, level):
        """image/* parser

        The only reason to make a specific parser for images is that,
        sometimes, messages embark inline images, which means they
        must be displayed and not attached.
        """
        if self.dformat == "html" and self.links \
                and "Content-Disposition" in msg:
            if msg["Content-Disposition"].startswith("inline"):
                cid = None
                if "Content-ID" in msg:
                    m = re.match("<(.+)>", msg["Content-ID"])
                    cid = m is not None and m.group(1) or msg["Content-ID"]
                fname = msg.get_filename()
                if fname is None:
                    if "Content-Location" in msg:
                        fname = msg["Content-Location"]
                    elif cid is not None:
                        fname = cid
                    else:
                        # I give up for now :p
                        return
                self.attached_map[cid] = re.match("^http:", fname) and fname \
                    or self.__save_image(fname, msg)
                return
        self._parse_default(msg, level)

    def _parse(self, msg, level=None):
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
        if msg.is_multipart() and msg.get_content_maintype() != "message":
            cpt = 1
            for part in msg.get_payload():
                nlevel = level is None and ("%d" % cpt) \
                    or "%s.%d" % (level, cpt)
                self._parse(part, nlevel)
                cpt += 1
            return

        if level is None:
            level = "1"
        try:
            getattr(self, "_parse_%s" % msg.get_content_maintype())(msg, level)
        except AttributeError:
            self._parse_default(msg, level)

    def __save_image(self, fname, part):
        """Save an inline image on the filesystem.

        Some HTML messages are using inline images (attached images
        with links on them inside the body). In order to display them,
        images are saved on the filesystem and links contained in the
        message are modified.

        :param fname: the image associated filename
        :param part: the email part that contains the image payload
        """
        if re.search(r"\.\.", fname):
            return None
        path = "/static/tmp/" + fname
        fp = open(settings.MODOBOA_DIR + path, "wb")
        fp.write(part.get_payload(decode=True))
        fp.close()
        return path

    def map_cid(self, url):
        """Replace attachment links.

        :param str url: original url
        :rtype: string
        :return: internal link
        """
        match = re.match(".*cid:(.+)", url)
        if match is not None:
            if match.group(1) in self.attached_map:
                return self.attached_map[match.group(1)]
        return url

    def render_headers(self, **kwargs):
        return render_to_string("common/mailheaders.html", {
            "headers": self.headers,
        })

    def viewmail_plain(self, content, **kwargs):
        return "<pre>%s</pre>" % content

    def viewmail_html(self, content, **kwargs):
        import lxml.html

        if content is None or content == "":
            return ""
        links = kwargs.get("links", 0)
        html = lxml.html.fromstring(content)
        if not links:
            html.rewrite_links(lambda x: None)
        else:
            html.rewrite_links(self.map_cid)
            for link in html.iterlinks():
                link[0].set('target', '_blank')
        body = html.find("body")
        if body is None:
            body = lxml.html.tostring(html)
        else:
            body = lxml.html.tostring(body)
            body = re.sub("<(/?)body", lambda m: "<%sdiv" % m.group(1), body)
        return body


def split_mailbox(mailbox, return_extension=False):
    """Try to split an address into parts (local part and domain name).

    If return_extension is True, we also look for an address extension
    (something foo+bar).

    :return: a tuple (local part, domain<, extension>)

    """
    domain = None
    if "@" not in mailbox:
        localpart = mailbox
    else:
        parts = mailbox.split("@")
        if len(parts) == 2:
            localpart = parts[0]
            domain = parts[1]
        else:
            domain = parts[-1]
            localpart = "@".join(parts[:-1])
    if not return_extension:
        return (localpart, domain)
    extension = None
    if "+" in localpart:
        localpart, extension = localpart.split("+", 1)
    return (localpart, domain, extension)


def decode(string, encodings=None, charset=None):
    """Try to decode the given string."""
    if encodings is None:
        encodings = ('utf8', 'latin1', 'windows-1252', 'ascii')
    if charset is not None:
        try:
            return string.decode(charset, 'ignore')
        except LookupError:
            pass

    for encoding in encodings:
        try:
            return string.decode(encoding)
        except UnicodeDecodeError:
            pass
    return string.decode('ascii', 'ignore')


def prepare_addresses(addresses, usage="header"):
    """Prepare addresses before using them

    FIXME: We need a real address parser here! If a name contains a
    separator, it creates two wrong addresses.

    :param list addresses: a list of addresses
    :param string usage: how those addresses are going to be used
    :return: a string or a list depending on usage value
    """
    result = []
    for address in re.split('[,;]', addresses):
        name, addr = parseaddr(address)
        if name and usage == "header":
            result.append("%s <%s>" % (Header(name, 'utf8').encode(), addr))
        else:
            result.append(addr)
    if usage == "header":
        return ",".join(result)
    return result


def set_email_headers(msg, subject, sender, rcpt):
    """Set mandatory headers.

    Subject, From, To, Message-ID, User-Agent, Date
    """
    import pkg_resources

    msg["Subject"] = Header(subject, 'utf8')
    msg["From"] = sender
    msg["To"] = prepare_addresses(rcpt)
    msg["Message-ID"] = make_msgid()
    msg["User-Agent"] = "Modoboa %s" % \
        (pkg_resources.get_distribution("modoboa").version)
    msg["Date"] = formatdate(time.time(), True)


def __sendmail(sender, rcpt, msgstring, server='localhost', port=25):
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
    except smtplib.SMTPException, e:
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
    msg = MIMEText(content, _charset='utf-8')
    set_email_headers(msg, subject, sender, rcpt)
    return __sendmail(sender, rcpt, msg.as_string(), **kwargs)


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
    except IOError, e:
        return False, str(e)

    content = """From: %s
To: %s
""" % (sender, rcpt)
    content += fp.read()
    fp.close()

    return __sendmail(sender, rcpt, content)
