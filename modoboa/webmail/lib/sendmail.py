from email.header import Header
from email.mime.image import MIMEImage
import os
import pkg_resources
import smtplib
from typing import Optional, Tuple
from urllib.parse import unquote, urlparse

import lxml

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives

from modoboa.core import models as core_models
from modoboa.parameters import tools as param_tools

from . import get_imapconnector


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


def make_body_images_inline(body: str) -> Tuple[str, list]:
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


def create_message(user: core_models.User, attributes: dict):
    headers = {
        "User-Agent": "Modoboa {}".format(
            pkg_resources.get_distribution("modoboa").version
        )
    }
    origmsgid = attributes.get("origmsgid")
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
    return msg


def send_mail(request, attributes: dict) -> Tuple[bool, Optional[str]]:
    """Email verification and sending.

    If the form does not present any error, a new MIME message is
    constructed. Then, a connection is established with the defined
    SMTP server and the message is finally sent.

    :param request: a Request object
    :param posturl: the url to post the message form to
    :return: a 2-uple (True|False, HttpResponse)
    """
    msg = create_message(request.user, attributes)
    conf = dict(param_tools.get_global_parameters("webmail"))
    options = {"host": conf["smtp_server"], "port": conf["smtp_port"]}
    if conf["smtp_secured_mode"] == "ssl":
        options.update({"use_ssl": True})
    elif conf["smtp_secured_mode"] == "starttls":
        options.update({"use_tls": True})
    if conf["smtp_authentication"]:
        if not settings.WEBMAIL_DEV_MODE:
            # TODO: oauth2 auth
            pass
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
    get_imapconnector(request).push_mail(sentfolder, msg.message())
    # clean_attachments(request.session["compose_mail"]["attachments"])
    # del request.session["compose_mail"]

    return True, None
