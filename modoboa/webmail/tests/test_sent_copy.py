"""Tests for the copies of the messages stored into the folders of the user."""

from unittest import mock

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import models
from modoboa.webmail.lib import sendmail
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"


class BccCopyTestCase(WebmailTestCase):
    """The copy keeps Bcc, the message sent never carries it."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _send(self, **extra):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        data = {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "bcc": ["hidden@example.test"],
            "subject": "test",
            "body": "Test",
            **extra,
        }
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        return push_mail.call_args.args[1]

    def test_sent_copy(self):
        copy = self._send()
        self.assertEqual(copy["Bcc"], "hidden@example.test")
        sent = mail.outbox[0]
        self.assertIsNone(sent.message()["Bcc"])
        self.assertIn("hidden@example.test", sent.recipients())

    def test_scheduled_copy(self):
        scheduled_datetime = timezone.now() + relativedelta(hours=1)
        copy = self._send(scheduled_datetime=scheduled_datetime.isoformat())
        self.assertEqual(copy["Bcc"], "hidden@example.test")

        message = models.ScheduledMessage.objects.get()
        with mock.patch.object(
            models.ScheduledMessage, "delete_imap_copy", return_value=True
        ):
            self.assertTrue(sendmail.send_scheduled_message(message))
        sent = mail.outbox[0]
        self.assertIsNone(sent.message()["Bcc"])
        self.assertIn("hidden@example.test", sent.recipients())
