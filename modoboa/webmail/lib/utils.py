"""Misc. utilities."""

import base64
import binascii
from email.header import Header
from email.mime.image import MIMEImage
from email.utils import formatdate, make_msgid
from importlib.metadata import version
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import lxml.etree
import lxml.html

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.mail.utils import DNS_NAME
from django.utils.html import escape
from django.utils.translation import gettext as _

from modoboa.core import models as core_models
from modoboa.webmail import constants
from modoboa.webmail.lib import flowed
from modoboa.webmail.lib.attachments import (
    create_mail_attachment,
    get_attachments_dir,
)


# Elements starting on a new line
_LINE_TAGS = {
    "address",
    "article",
    "aside",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "form",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "section",
    "table",
    "tr",
    "ul",
}
# Elements separated from the surrounding text by a blank line
_PARAGRAPH_TAGS = {"blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "p", "pre"}
# Elements whose content is never displayed
_HIDDEN_TAGS = {"head", "script", "style", "template", "title"}
# HTML whitespace: a non-breaking space is never collapsed
_WHITESPACE_RE = re.compile(r"[ \t\n\r\f]+")


class _PlainTextWriter:
    """Lay out the text of an HTML document line by line."""

    def __init__(self):
        self.lines: list[str] = []
        self.current = ""
        self.quote_depth = 0
        # Quote depth of the blank line to write before the next text
        self.pending_blank: int | None = None

    def _prefix(self, depth: int) -> str:
        # ">>" for nested quotes, as RFC 3676 (format=flowed) wants it
        return ">" * depth + " " if depth else ""

    def write(self, text: str, preformatted: bool = False) -> None:
        if not preformatted:
            text = _WHITESPACE_RE.sub(" ", text)
            if not self.current or self.current.endswith(" "):
                text = text.lstrip(" ")
            text = text.replace("\xa0", " ")
        for pos, chunk in enumerate(text.split("\n")):
            if pos:
                self.end_line(force=True)
            if not chunk:
                continue
            if not self.current and self.pending_blank is not None:
                if self.lines:
                    depth = min(self.pending_blank, self.quote_depth)
                    self.lines.append(self._prefix(depth).rstrip())
                self.pending_blank = None
            self.current += chunk

    def end_line(self, force: bool = False) -> None:
        if not self.current and not force:
            return
        content = self.current.rstrip()
        line = self._prefix(self.quote_depth) + content
        if content == "--":
            # The signature separator keeps its trailing space (RFC 3676)
            line += " "
        else:
            line = line.rstrip()
        self.lines.append(line)
        self.current = ""

    def end_paragraph(self) -> None:
        self.end_line()
        if self.pending_blank is None or self.pending_blank > self.quote_depth:
            self.pending_blank = self.quote_depth

    def text(self) -> str:
        self.end_line()
        return "\n".join(self.lines).strip("\n")


def _block_kind(element, tag: str | None) -> str | None:
    """Tell how an element is separated from the text around it."""
    parent = element.getparent()
    if tag in ("div", "p") and parent is not None and parent.tag == "li":
        # Rich text editors put the content of list items into paragraphs:
        # it must stay on the line of the item marker
        return "item"
    if tag in _PARAGRAPH_TAGS:
        return "paragraph"
    if tag in _LINE_TAGS:
        return "line"
    return None


def html2plaintext(content: str) -> str:
    """HTML to plain text translation.

    The text keeps the layout of the document: paragraphs, line breaks,
    lists and quotes (">" prefix). Link targets follow their text.

    :param content: some HTML content
    """
    if not content or not content.strip():
        return ""
    try:
        html = lxml.html.fromstring(content)
    except (lxml.etree.ParserError, ValueError):
        return ""
    writer = _PlainTextWriter()
    hidden = 0
    preformatted = 0
    # Item counters of the enclosing lists (None for bulleted ones)
    lists: list[int | None] = []
    events = ("start", "end", "comment", "pi")
    for event, element in lxml.etree.iterwalk(html, events=events):
        tag = element.tag if isinstance(element.tag, str) else None
        if event == "start":
            if tag in _HIDDEN_TAGS:
                hidden += 1
            if hidden:
                continue
            kind = _block_kind(element, tag)
            if kind == "paragraph":
                writer.end_paragraph()
            elif kind == "line":
                writer.end_line()
            elif kind == "item" and (
                element.getprevious() is not None
                or (element.getparent().text or "").strip()
            ):
                # Not the first content of the item
                writer.end_line()
            if tag == "blockquote":
                writer.quote_depth += 1
            elif tag == "pre":
                preformatted += 1
            elif tag == "br":
                writer.end_line(force=True)
            elif tag == "hr":
                writer.write("----")
            elif tag == "img" and element.get("alt"):
                writer.write(element.get("alt"))
            elif tag in ("ol", "ul"):
                lists.append(0 if tag == "ol" else None)
            elif tag == "li":
                indent = "  " * max(len(lists) - 1, 0)
                if lists and lists[-1] is not None:
                    lists[-1] += 1
                    writer.write(f"{indent}{lists[-1]}. ", preformatted=True)
                else:
                    writer.write(f"{indent}- ", preformatted=True)
            if element.text:
                writer.write(element.text, preformatted > 0)
            continue
        if tag in _HIDDEN_TAGS:
            hidden -= 1
        elif not hidden and event == "end":
            if tag == "a":
                href = element.get("href", "")
                label = element.text_content().strip()
                if (
                    href
                    and not href.startswith(("#", "javascript:"))
                    and href not in (label, f"mailto:{label}")
                ):
                    writer.write(f" <{href}>")
            elif tag in ("td", "th"):
                writer.write(" ")
            elif tag in ("ol", "ul") and lists:
                lists.pop()
            kind = _block_kind(element, tag)
            if kind == "paragraph":
                writer.end_paragraph()
            elif kind in ("line", "item"):
                writer.end_line()
            if tag == "blockquote":
                writer.quote_depth -= 1
            elif tag == "pre":
                preformatted -= 1
        if element.tail and not hidden and element is not html:
            writer.write(element.tail, preformatted > 0)
    return writer.text()


_QUOTE_RE = re.compile(r"^(?:> ?)+")


def plaintext2html(content: str) -> str:
    """Plain text to HTML translation, for the editor.

    Blank lines separate paragraphs, line breaks are kept and quoted lines
    (">" prefix) go into blockquotes.

    :param content: some plain text content
    """
    if not content:
        return ""
    result = ""
    depth = 0
    paragraph: list[str] = []

    def flush() -> str:
        if not paragraph:
            return ""
        html = f"<p>{'<br>'.join(paragraph)}</p>"
        paragraph.clear()
        return html

    for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        match = _QUOTE_RE.match(line)
        quote = match.group(0) if match else ""
        line_depth = quote.count(">")
        text = line[len(quote) :]
        if line_depth != depth:
            result += flush()
            if line_depth > depth:
                result += "<blockquote>" * (line_depth - depth)
            else:
                result += "</blockquote>" * (depth - line_depth)
            depth = line_depth
        if not text.strip():
            result += flush()
            continue
        text = escape(text)
        # Keep the indentation, that HTML would collapse
        indent = len(text) - len(text.lstrip(" "))
        paragraph.append("&nbsp;" * indent + text[indent:])
    result += flush()
    result += "</blockquote>" * depth
    return result


def convert_body(content: str, source: str, target: str) -> str:
    """Convert a message body from a format (plain or html) to another."""
    if not content or source == target:
        return content
    if target == "html":
        return plaintext2html(content)
    return html2plaintext(content)


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


# An image embedded into the HTML content
_DATA_URI_RE = re.compile(r"data:(image/[\w.+-]+);base64,(.*)", re.I | re.S)


def _data_uri_image(src: str, parts: dict) -> str | None:
    """Turn an image given as a data: URI into a part of the message.

    The editor shows the embedded images of replies, forwards and drafts
    as data: URIs, that many clients refuse to display.

    :param parts: the parts already created, by Content-ID (the same image
        is attached once)
    :return: the Content-ID of the part, None if the URI is not a valid image
    """
    match = _DATA_URI_RE.match(src)
    if not match:
        return None
    content_type = match.group(1).lower()
    if content_type not in constants.INLINE_IMAGE_MIME_TYPES:
        return None
    try:
        payload = base64.b64decode(match.group(2), validate=False)
    except (binascii.Error, ValueError):
        return None
    if not payload:
        return None
    subtype = content_type.split("/")[1]
    cid = f"{hashlib.sha256(payload).hexdigest()[:24]}@modoboa"
    if cid not in parts:
        part = MIMEImage(payload, _subtype=subtype)
        part["Content-ID"] = f"<{cid}>"
        part.set_param("name", f"{cid.split('@')[0]}.{subtype}")
        part["Content-Disposition"] = "inline"
        parts[cid] = part
    return cid


def make_body_images_inline(body: str) -> tuple[str, list]:
    """Look for images inside the body and make them inline.

    Before sending a message in HTML format, it is necessary to find
    all img tags contained in the body in order to rewrite them. For
    example, icons provided by CKeditor are stored on the server
    filesystem and not accessible from the outside. We must embark
    them as parts of the MIME message if we want recipients to
    display them correctly.

    :param body: the HTML body to parse
    """
    html = lxml.html.fromstring(body)
    parts = []
    embedded: dict = {}
    root = Path(settings.BASE_DIR).resolve()
    # Never embed private files: attachments of any user, and the legacy
    # webmail media directory (inline images and uploads of other users).
    private_dirs = [
        Path(get_attachments_dir()).resolve(),
        (Path(settings.MEDIA_ROOT) / "webmail").resolve(),
    ]
    for tag in html.iter("img"):
        src = tag.get("src")
        if src is None:
            continue
        if src[:5].lower() == "data:":
            cid = _data_uri_image(src, embedded)
            if cid is not None:
                tag.set("src", f"cid:{cid}")
            continue
        o = urlparse(src)
        # Only handle local references, never remote URLs.
        if o.scheme or o.netloc:
            continue
        # Resolve the candidate path and make sure it stays inside BASE_DIR,
        # otherwise an attacker could use ../ segments to read arbitrary
        # local files (path traversal, CWE-22).
        candidate = (root / unquote(o.path.lstrip("/"))).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if any(candidate.is_relative_to(private) for private in private_dirs):
            continue
        if not candidate.is_file():
            continue
        try:
            with candidate.open("rb") as fp:
                part = MIMEImage(fp.read())
        except (OSError, TypeError):
            # Unreadable file or unrecognized image format: skip it instead
            # of aborting the whole send/save operation.
            continue
        fname = candidate.name
        cid = f"{os.path.splitext(fname)[0]}@modoboa"
        tag.set("src", f"cid:{cid}")
        part["Content-ID"] = f"<{cid}>"
        part.replace_header("Content-Type", f'{part["Content-Type"]}; name="{fname}"')
        part["Content-Disposition"] = "inline"
        parts.append(part)
    parts += embedded.values()
    return lxml.html.tostring(html, encoding="unicode"), parts


def _set_flowed(msg) -> None:
    """Declare the text part of a MIME message as format=flowed."""
    for part in msg.walk():
        if part.get_content_type() == "text/plain" and not part.get(
            "Content-Disposition"
        ):
            part.set_param("format", "flowed")
            return


class FlowedEmailMessage(EmailMessage):
    """A message whose text is sent as format=flowed (RFC 3676)."""

    def message(self, *args, **kwargs):
        msg = super().message(*args, **kwargs)
        _set_flowed(msg)
        return msg


class FlowedEmailMultiAlternatives(EmailMultiAlternatives):
    """A message whose text alternative is sent as format=flowed."""

    def message(self, *args, **kwargs):
        msg = super().message(*args, **kwargs)
        _set_flowed(msg)
        return msg


def html_msg(body: str) -> EmailMultiAlternatives:
    """Create a multipart message.

    We attach two alternatives:
    * text/html
    * text/plain
    """
    if body:
        tbody = html2plaintext(body)
        body, images = make_body_images_inline(body)
    else:
        tbody = ""
        images = []
    msg = FlowedEmailMultiAlternatives()
    msg.body = flowed.encode(tbody)
    msg.attach_alternative(body, "text/html")
    for img in images:
        msg.attach(img)
    return msg


def plain_msg(body: str) -> EmailMessage:
    """Create a simple text message."""
    msg = FlowedEmailMessage()
    msg.body = flowed.encode(body)
    return msg


def format_sender_address(user: core_models.User, address: str) -> str:
    """Format address before message is sent."""
    if user.first_name != "" or user.last_name != "":
        return f'"{Header(user.fullname, "utf8")}" <{address}>'
    return address


def allowed_sender_addresses(user: core_models.User) -> set[str]:
    """Return the addresses the user may send from, lowercased."""
    allowed = {user.email}
    mailbox = getattr(user, "mailbox", None)
    if mailbox is not None:
        allowed.update(mailbox.alias_addresses)
        allowed.update(mailbox.senderaddress_set.values_list("address", flat=True))
    return {address.lower() for address in allowed if address}


def check_sender_address(user: core_models.User, address: str) -> str | None:
    """Tell why the user may not send from this address, None if they may.

    Rights change between the moment a message is scheduled and the moment
    it leaves: the account or its domain can be disabled, the mailbox or an
    alias can be removed. The relay used for scheduled sendings does not
    authenticate, so nothing else would notice.
    """
    if not user.is_active:
        return _("The account has been disabled")
    mailbox = getattr(user, "mailbox", None)
    if mailbox is None:
        return _("The mailbox no longer exists")
    if not mailbox.domain.enabled:
        return _("The domain has been disabled")
    if address.lower() not in allowed_sender_addresses(user):
        return _("This address is no longer allowed for this account")
    return None


def build_references(references: str, in_reply_to: str) -> str:
    """Build the References header of a reply.

    It holds the References of the parent message followed by the parent
    Message-ID (RFC 5322, section 3.6.4), so that clients can rebuild the
    whole thread.
    """
    result = references.split()
    if not result or result[-1] != in_reply_to:
        result.append(in_reply_to)
    return " ".join(result)


def build_message_id(sender: str) -> str:
    """Return a new Message-ID, in the domain of the sender address."""
    domain = sender.rpartition("@")[2]
    try:
        domain = domain.encode("idna").decode("ascii")
    except UnicodeError:
        domain = ""
    return make_msgid(domain=domain or str(DNS_NAME))


def create_message(
    user: core_models.User, attributes: dict, attachments: list
) -> EmailMessage:
    """Create an EmailMessage instance ready to be sent.

    Its Message-ID and Date are set once and for all: Django would build
    new ones each time the MIME message is generated, and the copy saved
    into the Sent folder would not be the message actually sent.

    Optional attributes: "message_id" and "date" (a datetime), for a
    message built several times (scheduled sending).
    """
    date = attributes.get("date")
    extra_headers = {
        "User-Agent": "Modoboa {}".format(version("modoboa")),
        "Message-ID": attributes.get("message_id")
        or build_message_id(attributes["sender"]),
        "Date": formatdate(
            date.timestamp() if date else None,
            localtime=settings.EMAIL_USE_LOCALTIME,
        ),
    }
    if attributes.get("request_mdn"):
        extra_headers["Disposition-Notification-To"] = format_sender_address(
            user, attributes["sender"]
        )
    origmsgid = attributes.get("in_reply_to")
    if origmsgid:
        extra_headers.update(
            {
                "References": build_references(
                    attributes.get("references", ""), origmsgid
                ),
                "In-Reply-To": origmsgid,
            }
        )
    # The format chosen while writing wins over the preference
    mode = attributes.get("body_format") or user.parameters.get_value("editor")
    sender = format_sender_address(user, attributes["sender"])
    if mode == "html":
        msg = html_msg(attributes.get("body", ""))
    else:
        msg = plain_msg(attributes.get("body", ""))
    msg.from_email = sender
    msg.to = attributes.get("to", [])
    msg.extra_headers = extra_headers
    for hdr in ["subject", "cc", "bcc"]:
        if hdr in attributes:
            setattr(msg, hdr, attributes[hdr])

    for attachment in attachments:
        msg.attach(create_mail_attachment(attachment))
    return msg
