"""Misc. utilities."""

from email.header import Header
from email.mime.image import MIMEImage
from importlib.metadata import version
import os
from urllib.parse import unquote, urlparse

import lxml

from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives

from modoboa.core import models as core_models
from modoboa.webmail.lib.attachments import create_mail_attachment


def html2plaintext(content: str) -> str:
    """HTML to plain text translation.

    :param content: some HTML content
    """
    if not content:
        return ""
    html = lxml.html.fromstring(content)
    plaintext = ""
    for ch in html.iter():
        p = None
        if ch.text is not None:
            p = ch.text.strip("\r\t\n")
        if ch.tag == "img":
            p = ch.get("alt")
        if p is None:
            continue
        plaintext += p + "\n"
    return plaintext


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
    for tag in html.iter("img"):
        src = tag.get("src")
        if src is None:
            continue
        o = urlparse(src)
        path = unquote(os.path.join(settings.BASE_DIR, o.path[1:]))
        if not os.path.exists(path):
            continue
        fname = os.path.basename(path)
        cid = f"{os.path.splitext(fname)[0]}@modoboa"
        tag.set("src", f"cid:{cid}")
        with open(path, "rb") as fp:
            part = MIMEImage(fp.read())
        part["Content-ID"] = f"<{cid}>"
        part.replace_header("Content-Type", f'{part["Content-Type"]}; name="{fname}"')
        part["Content-Disposition"] = "inline"
        parts.append(part)
    return lxml.html.tostring(html, encoding="unicode"), parts


def html_msg(content: str) -> EmailMultiAlternatives:
    """Create a multipart message.

    We attach two alternatives:
    * text/html
    * text/plain
    """
    if content:
        body = html2plaintext(content)
        body, images = make_body_images_inline(body)
    else:
        body = ""
        images = []
    msg = EmailMultiAlternatives()
    msg.body = body
    msg.attach_alternative(body, "text/html")
    for img in images:
        msg.attach(img)
    return msg


def plain_msg(content: str) -> EmailMessage:
    """Create a simple text message."""
    msg = EmailMessage()
    msg.body = content
    return msg


def format_sender_address(user: core_models.User, address: str) -> str:
    """Format address before message is sent."""
    if user.first_name != "" or user.last_name != "":
        return f'"{Header(user.fullname, "utf8")}" <{address}>'
    return address


def create_message(
    user: core_models.User, attributes: dict, attachments: list
) -> EmailMessage:
    """Create an EmailMessage instance ready to be sent."""
    extra_headers = {"User-Agent": "Modoboa {}".format(version("modoboa"))}
    headers = {}
    origmsgid = attributes.get("in_reply_to")
    if origmsgid:
        headers.update({"References": origmsgid, "In-Reply-To": origmsgid})
    mode = user.parameters.get_value("editor")
    sender = format_sender_address(user, attributes["sender"])
    if mode == "html":
        msg = html_msg(attributes.get("body", ""))
    else:
        msg = plain_msg(attributes.get("body", ""))
    msg.from_email = sender
    msg.to = attributes["to"]
    msg.headers = headers
    msg.extra_headers = extra_headers
    for hdr in ["subject", "cc", "bcc"]:
        if hdr in attributes:
            setattr(msg, hdr, attributes[hdr])

    for attachment in attachments:
        msg.attach(create_mail_attachment(attachment))
    return msg
