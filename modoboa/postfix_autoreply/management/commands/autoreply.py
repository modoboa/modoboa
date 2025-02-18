import datetime
import email
import email.header
import fileinput
from io import StringIO
import logging
import smtplib
import sys
from logging.handlers import SysLogHandler

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone, translation
from django.utils.encoding import smart_str
from django.utils.formats import localize

from modoboa.admin.models import Mailbox
from modoboa.lib.email_utils import split_mailbox
from modoboa.parameters import tools as param_tools
from ...models import ARhistoric, ARmessage

logger = logging.getLogger()


def safe_subject(msg):
    """Clean message subject and return it."""
    decoded = email.header.decode_header(msg.get("Subject"))
    subject = ""
    for sub, charset in decoded:
        if isinstance(sub, str):
            subject += sub
            continue
        # charset can be None
        charset = charset if charset else "utf-8"
        try:
            subject += sub.decode(charset)
        except UnicodeDecodeError:
            pass
    return " ".join(subject.split())


def send_autoreply(sender, mailbox, armessage, original_msg):
    """Send an autoreply message."""
    if armessage.fromdate > timezone.now():
        # Too soon, come back later
        return

    condition = armessage.untildate is not None and armessage.untildate < timezone.now()
    if condition:
        # ARmessage has expired, disable it
        armessage.enabled = False
        armessage.save(update_fields=["enabled"])
        return

    try:
        lastar = ARhistoric.objects.get(armessage=armessage.id, sender=sender)
        timeout = param_tools.get_global_parameter(
            "autoreplies_timeout", app="postfix_autoreply"
        )
        delta = datetime.timedelta(seconds=int(timeout))
        now = timezone.make_aware(
            datetime.datetime.now(), timezone.get_default_timezone()
        )
        if lastar.last_sent + delta > now:
            logger.debug(
                "no autoreply message sent because delta (%s) < timetout (%s)",
                delta,
                timeout,
            )
            return

    except ARhistoric.DoesNotExist:
        lastar = ARhistoric()
        lastar.armessage = armessage
        lastar.sender = sender

    headers = {"Auto-Submitted": "auto-replied", "Precedence": "bulk"}
    message_id = original_msg.get("Message-ID", "").strip("\n")
    if message_id:
        headers.update({"In-Reply-To": message_id, "References": message_id})

    subject = safe_subject(original_msg)
    with translation.override(mailbox.user.language):
        context = {
            "name": mailbox.user.fullname,
            "fromdate": localize(armessage.fromdate),
            "untildate": "",
        }
        if armessage.untildate:
            context.update({"untildate": localize(armessage.untildate)})
    content = armessage.content % context
    msg = EmailMessage(
        f"Auto: {armessage.subject} Re: {subject}",
        smart_str(content),
        mailbox.user.encoded_address,
        [sender],
        headers=headers,
    )
    try:
        msg.send()
    except smtplib.SMTPException as exp:
        logger.error("Failed to send autoreply message: %s", exp)
        sys.exit(1)

    logger.debug("autoreply message sent to %s", mailbox.user.encoded_address)

    lastar.last_sent = datetime.datetime.now()
    lastar.save()


class Command(BaseCommand):
    """Command definition."""

    help = "Send autoreply emails"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument("--debug", action="store_true", dest="debug", default=False)
        parser.add_argument(
            "--syslog-socket-path", default="/dev/log", help="Path to syslog socket"
        )
        parser.add_argument("sender")
        parser.add_argument("recipient", nargs="+")

    def handle(self, *args, **options):
        try:
            handler = SysLogHandler(address=options["syslog_socket_path"])
        except OSError as ex:
            if ex.errno == 2:
                # try the default, localhost:514
                handler = SysLogHandler()
            else:
                raise

        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        if options["debug"]:
            logger.setLevel(logging.DEBUG)

        logger.debug(
            "autoreply sender=%s recipient=%s",
            options["sender"],
            ",".join(options["recipient"]),
        )

        sender = smart_str(options["sender"])

        sender_localpart = split_mailbox(sender.lower())[0]
        if (
            (sender_localpart in ("mailer-daemon", "listserv", "majordomo"))
            or (sender_localpart.startswith("owner-"))
            or (sender_localpart.endswith("-request"))
        ):
            logger.debug("Skip auto reply, this mail comes from a mailing list")
            return

        content = StringIO()
        for line in fileinput.input([]):
            content.write(line)
        content.seek(0)

        original_msg = email.message_from_file(content)

        # Mailing list filter based on
        # https://tools.ietf.org/html/rfc5230#page-7
        ml_known_headers = [
            "List-Id",
            "List-Help",
            "List-Subscribe",
            "List-Unsubscribe",
            "List-Post",
            "List-Owner",
            "List-Archive",
        ]
        from_ml = False
        for header in ml_known_headers:
            if header in original_msg:
                from_ml = True
                break
        condition = (
            original_msg.get("Precedence") == "bulk"
            or original_msg.get("X-Mailer") == "PHPMailer"
            or from_ml
        )
        if condition:
            logger.debug("Skip auto reply, this mail comes from a mailing list")
            return

        recipients = [smart_str(rcpt) for rcpt in options["recipient"]]
        for fulladdress in recipients:
            address, domain = split_mailbox(fulladdress)
            try:
                mbox = Mailbox.objects.get(address=address, domain__name=domain)
            except Mailbox.DoesNotExist:
                msg = f"Unknown recipient {fulladdress}"
                logger.debug("autoreply %s", msg)
                continue
            try:
                armessage = ARmessage.objects.get(mbox=mbox.id, enabled=True)
                logger.debug("autoreply message found")
            except ARmessage.DoesNotExist:
                logger.debug("autoreply message not found")
                continue

            send_autoreply(sender, mbox, armessage, original_msg)
