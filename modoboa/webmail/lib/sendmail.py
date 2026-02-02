import smtplib

from django.conf import settings
from django.core import mail

from modoboa.parameters import tools as param_tools
from modoboa.webmail import constants, models
from modoboa.webmail.exceptions import WebmailInternalError
from modoboa.webmail.lib.utils import create_message

from . import get_imapconnector


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
                    "password": str(request.auth),
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


def schedule_email(
    request, attributes: dict, attachments: list
) -> models.ScheduledMessage:
    """Schedule a new email sending."""
    sched_msg = models.ScheduledMessage(
        account=request.user,
        sender=attributes["sender"],
        scheduled_datetime=attributes["scheduled_datetime"],
        to=",".join(attributes["to"]),
        subject=attributes.get("subject", ""),
        body=attributes.get("body", ""),
        in_reply_to=attributes.get("in_reply_to", ""),
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
            msg.connection = connection
            msg.send()
    except (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused) as inst:
        if isinstance(inst, smtplib.SMTPRecipientsRefused):
            error = ", ".join(
                [f"{rcpt}: {error}" for rcpt, error in inst.recipients.items()]
            )
        else:
            error = str(inst.smtp_error)
        sched_msg.status = constants.SchedulingState.SEND_ERROR.value
        sched_msg.error = error
        sched_msg.save()
        return False

    return sched_msg.delete_imap_copy()
