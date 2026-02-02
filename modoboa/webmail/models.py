"""
Webmail related models.
"""

from django.core.mail import EmailMessage
from django.db import models

from modoboa.lib.sysutils import doveadm_cmd
from modoboa.webmail import constants
from modoboa.webmail.lib.utils import create_message


class ScheduledMessage(models.Model):
    account = models.ForeignKey("core.User", on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    to = models.TextField()
    cc = models.TextField(blank=True, null=True)
    bcc = models.TextField(blank=True, null=True)
    in_reply_to = models.CharField(max_length=200, blank=True, null=True)
    scheduled_datetime = models.DateTimeField()
    imap_uid = models.IntegerField(blank=True, null=True)
    status = models.CharField(
        choices=constants.EMAIL_SCHEDULING_STATES,
        default=constants.SchedulingState.SCHEDULED.value,
        max_length=15,
        db_index=True,
    )
    error = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.subject} - {self.sender.username} - {self.scheduled_datetime}"

    def to_dict(self) -> dict:
        result = {
            "in_reply_to": self.in_reply_to,
            "sender": self.sender,
            "to": self.to.split(","),
        }
        if self.subject:
            result["subject"] = self.subject
        if self.body:
            result["body"] = self.body
        for hdr in ["cc", "bcc"]:
            if getattr(self, hdr):
                result[hdr] = getattr(self, hdr).split(",")
        return result

    def delete_imap_copy(self) -> bool:
        """Move IMAP message to Sent folder using doveadm."""
        # TODO: use doveadm HTTP API when dovecot is not local
        sent_folder = self.account.parameters.get_value("sent_folder")
        code, output = doveadm_cmd(
            f"move -u {self.account.email} {sent_folder} "
            f"mailbox {constants.MAILBOX_NAME_SCHEDULED} "
            f"header {constants.CUSTOM_HEADER_SCHEDULED_ID} {self.id}"
        )
        if code:
            self.status = constants.SchedulingState.MOVE_ERROR.value
            self.error = output
            self.save()
            return False

        return True

    def to_email_message(self) -> EmailMessage:
        """Convert this scheduled message to an EmailMessage instance."""
        attachments = [attachment.to_dict() for attachment in self.attachments.all()]
        result = create_message(self.account, self.to_dict(), attachments)
        result.extra_headers.update(
            {
                constants.CUSTOM_HEADER_SCHEDULED_ID: self.id,
                constants.CUSTOM_HEADER_SCHEDULED_DATETIME: self.scheduled_datetime.isoformat(),
            }
        )
        return result


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        ScheduledMessage, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField()
    content_type = models.CharField(max_length=150)
    filename = models.CharField(max_length=255)

    def __str__(self):
        return f"Attachment for {self.message.subject}"

    def to_dict(self) -> dict:
        return {
            "content-type": self.content_type,
            "tmpname": self.file.name,
            "fname": self.filename,
        }
