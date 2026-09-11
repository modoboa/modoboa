import logging
import smtplib

from django.conf import settings
from django.core import mail

from modoboa.lib.oauth2 import get_access_token
from modoboa.parameters import tools as param_tools
from modoboa.webmail import constants, models
from modoboa.webmail.exceptions import ImapError, WebmailInternalError
from modoboa.webmail.lib.utils import create_message

from . import get_imapconnector

logger = logging.getLogger("modoboa.webmail")


def get_smtp_error_message(error: OSError) -> str:
    """Return a readable message for an SMTP or network error.

    smtplib errors are ``OSError`` subclasses, like the network errors
    (connection refused, timeout, TLS failure...) raised while talking
    to the server.
    """
    if isinstance(error, smtplib.SMTPRecipientsRefused):
        return ", ".join(
            [f"{rcpt}: {reason}" for rcpt, reason in error.recipients.items()]
        )
    if isinstance(error, smtplib.SMTPResponseException):
        smtp_error = error.smtp_error
        if isinstance(smtp_error, bytes):
            smtp_error = smtp_error.decode(errors="replace")
        return str(smtp_error)
    return str(error) or error.__class__.__name__


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
        dev_mode = getattr(settings, "WEBMAIL_DEV_MODE", False)
        if not dev_mode:
            options.update(
                {
                    "backend": "modoboa.lib.smtp_backend.OAuthBearerEmailBackend",
                    "username": request.user.email,
                    "password": get_access_token(request),
                }
            )
        else:
            options.update(
                {
                    "username": settings.WEBMAIL_DEV_USERNAME,
                    "password": settings.WEBMAIL_DEV_PASSWORD,
                }
            )
    request_dsn = attributes.get("request_dsn", False)
    try:
        with mail.get_connection(**options) as connection:
            if request_dsn:
                connection.open()
                from_email = msg.from_email
                recipients = msg.recipients()
                message_data = msg.message().as_bytes(linesep="\r\n")
                connection.connection.sendmail(
                    from_email,
                    recipients,
                    message_data,
                    mail_options=["RET=HDRS"],
                    rcpt_options=["NOTIFY=SUCCESS,FAILURE,DELAY"],
                )
            else:
                msg.connection = connection
                msg.send()
    except OSError as error:
        return False, get_smtp_error_message(error)

    # Copy message to sent folder
    sentfolder = request.user.parameters.get_value("sent_folder")
    try:
        with get_imapconnector(request) as imapc:
            imapc.push_mail(sentfolder, msg.message())
    except (ImapError, WebmailInternalError):
        # The message is sent: reporting a failure would make the user
        # send it again.
        logger.exception("Failed to store a copy of the sent message")
    return True, None


def schedule_email(
    request, attributes: dict, attachments: list
) -> models.ScheduledMessage:
    """Schedule a new email sending."""
    scheduled_datetime = attributes["scheduled_datetime"].replace(
        second=0, microsecond=0
    )
    sched_msg = models.ScheduledMessage(
        account=request.user,
        sender=attributes["sender"],
        scheduled_datetime=scheduled_datetime,
        to=",".join(attributes["to"]),
        subject=attributes.get("subject", ""),
        body=attributes.get("body", ""),
        in_reply_to=attributes.get("in_reply_to", ""),
        request_dsn=attributes.get("request_dsn", False),
        request_mdn=attributes.get("request_mdn", False),
    )
    for attr in ["cc", "bcc"]:
        if attr in attributes:
            setattr(sched_msg, attr, ",".join(attributes[attr]))
    sched_msg.save()

    # Save a copy of this message into an IMAP mailbox
    msg = sched_msg.to_email_message()
    with get_imapconnector(request) as imapc:
        try:
            imapc.create_folder(constants.MAILBOX_NAME_SCHEDULED)
        except WebmailInternalError:
            pass
        # TODO: deal with UID Validity
        sched_msg.imap_uid = imapc.push_mail(
            constants.MAILBOX_NAME_SCHEDULED, msg.message()
        )
        sched_msg.save()

    for attachment in attachments:
        mattachment = models.MessageAttachment(
            message=sched_msg,
        )
        for header in ["content-type", "Content-Type"]:
            if header in attachment:
                mattachment.content_type = attachment[header]
                break
        if not mattachment.content_type:
            continue

        mattachment.file.name = attachment["tmpname"]
        if "fname" in attachment:
            mattachment.filename = attachment["fname"]
        mattachment.save()

    return sched_msg


def send_scheduled_message(sched_msg: models.ScheduledMessage) -> bool:
    """Send a scheduled message using configured SMTP server."""
    msg = sched_msg.to_email_message()
    conf = dict(param_tools.get_global_parameters("webmail"))
    options = {
        "host": conf["scheduling_smtp_server"],
        "port": conf["scheduling_smtp_port"],
    }
    if conf["scheduling_smtp_secured_mode"] == "ssl":
        options.update({"use_ssl": True})
    elif conf["scheduling_smtp_secured_mode"] == "starttls":
        options.update({"use_tls": True})

    try:
        with mail.get_connection(**options) as connection:
            if sched_msg.request_dsn:
                connection.open()
                from_email = msg.from_email
                recipients = msg.recipients()
                message_data = msg.message().as_bytes(linesep="\r\n")
                connection.connection.sendmail(
                    from_email,
                    recipients,
                    message_data,
                    mail_options=["RET=HDRS"],
                    rcpt_options=["NOTIFY=SUCCESS,FAILURE,DELAY"],
                )
            else:
                msg.connection = connection
                msg.send()
    except OSError as error:
        max_length = models.ScheduledMessage._meta.get_field("error").max_length
        sched_msg.status = constants.SchedulingState.SEND_ERROR.value
        sched_msg.error = get_smtp_error_message(error)[:max_length]
        sched_msg.save()
        return False

    return sched_msg.delete_imap_copy()
