from email.header import Header
from email.mime.image import MIMEImage
from importlib.metadata import version
import os

import smtplib
from urllib.parse import unquote, urlparse

import lxml

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives

from modoboa.core import models as core_models
from modoboa.parameters import tools as param_tools
from modoboa.webmail.lib.attachments import create_mail_attachment
from modoboa.webmail.lib.utils import html2plaintext

from . import get_imapconnector


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


def html_msg(attributes: dict) -> EmailMultiAlternatives:
    """Create a multipart message.

    We attach two alternatives:
    * text/html
    * text/plain
    """
    body = attributes.get("body")
    if body:
        tbody = html2plaintext(body)
        body, images = make_body_images_inline(body)
    else:
        tbody = ""
        images = []
    msg = EmailMultiAlternatives()
    msg.body = tbody
    msg.attach_alternative(body, "text/html")
    for img in images:
        msg.attach(img)
    return msg


def plain_msg(attributes: dict) -> EmailMessage:
    """Create a simple text message."""
    msg = EmailMessage()
    msg.body = attributes.get("body", "")
    return msg


def format_sender_address(user: core_models.User, address: str) -> str:
    """Format address before message is sent."""
    if user.first_name != "" or user.last_name != "":
        return f'"{Header(user.fullname, "utf8")}" <{address}>'
    return address


def create_message(user: core_models.User, attributes: dict, attachments: list):
    headers = {"User-Agent": "Modoboa {}".format(version("modoboa"))}
    origmsgid = attributes.get("in_reply_to")
    if origmsgid:
        headers.update({"References": origmsgid, "In-Reply-To": origmsgid})
    mode = user.parameters.get_value("editor")
    sender = format_sender_address(user, attributes["sender"])
    if mode == "html":
        msg = html_msg(attributes)
    else:
        msg = plain_msg(attributes)
    msg.from_email = sender
    msg.to = attributes["to"]
    msg.headers = headers
    for hdr in ["subject", "cc", "bcc"]:
        if hdr in attributes:
            setattr(msg, hdr, attributes[hdr])

    for attachment in attachments:
        msg.attach(create_mail_attachment(attachment))
    return msg


def send_mail(request, attributes: dict, attachments: list) -> tuple[bool, str | None]:
    """
    Send a new email.

    A new MIME message is first constructed. Then, a connection is established with the defined
    SMTP server and the message is finally sent.
    """
    msg = create_message(request.user, attributes, attachments)
    conf = dict(param_tools.get_global_parameters("webmail"))
    options = {"host": conf["smtp_server"], "port": conf["smtp_port"]}
    if conf["smtp_secured_mode"] == "ssl":
        options.update({"use_ssl": True})
    elif conf["smtp_secured_mode"] == "starttls":
        options.update({"use_tls": True})
    if conf["smtp_authentication"]:
        if not settings.WEBMAIL_DEV_MODE:
            options.update(
                {
                    "backend": "modoboa.lib.smtp_backend.OAuthBearerEmailBackend",
                    "username": request.user.email,
                    "password": request.auth,
                }
            )
        else:
            options.update(
                {
                    "username": settings.WEBMAIL_DEV_USERNAME,
                    "password": settings.WEBMAIL_DEV_PASSWORD,
                }
            )
    try:
        with mail.get_connection(**options) as connection:
            msg.connection = connection
            msg.send()
    except smtplib.SMTPResponseException as inst:
        return False, str(inst.smtp_error)
    except smtplib.SMTPRecipientsRefused as inst:
        error = ", ".join(
            [f"{rcpt}: {error}" for rcpt, error in inst.recipients.items()]
        )
        return False, error

    # Copy message to sent folder
    sentfolder = request.user.parameters.get_value("sent_folder")
    with get_imapconnector(request) as imapc:
        imapc.push_mail(sentfolder, msg.message())
    return True, None
