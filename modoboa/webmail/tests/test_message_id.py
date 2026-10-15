"""Tests for the Message-ID and Date of the messages sent."""

from email.utils import formatdate
from unittest import mock

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import constants, factories, models
from modoboa.webmail.lib import sendmail, utils
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"


class MessageIdTestCase(WebmailTestCase):
    """The copy of a message must have the Message-ID of the message sent."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _data(self, **extra):
        return {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "subject": "test",
            "body": "Test",
            **extra,
        }

    def _send(self, **extra):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        return self.client.post(url, self._data(**extra), format="json")

    def test_headers_are_set_once(self):
        msg = utils.create_message(self.user, self._data(), [])
        first = msg.message()
        second = msg.message()
        self.assertEqual(first["Message-ID"], second["Message-ID"])
        self.assertEqual(first["Date"], second["Date"])
        domain = self.user.email.split("@")[1]
        self.assertTrue(first["Message-ID"].endswith(f"@{domain}>"))

    def test_given_headers_are_kept(self):
        date = timezone.now() + relativedelta(days=1)
        msg = utils.create_message(
            self.user, self._data(message_id="<id@test.com>", date=date), []
        ).message()
        self.assertEqual(msg["Message-ID"], "<id@test.com>")
        self.assertEqual(
            msg["Date"],
            formatdate(date.timestamp(), localtime=settings.EMAIL_USE_LOCALTIME),
        )

    def test_sent_copy_has_the_same_message_id(self):
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self._send()
        self.assertEqual(response.status_code, 204)
        copy = push_mail.call_args.args[1]
        sent = mail.outbox[0].message()
        self.assertEqual(copy["Message-ID"], sent["Message-ID"])
        self.assertEqual(copy["Date"], sent["Date"])


class ScheduledMessageTestCase(WebmailTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _schedule(self, **extra):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        data = {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "subject": "test",
            "body": "Test",
            "scheduled_datetime": (timezone.now() + relativedelta(hours=1)).isoformat(),
            **extra,
        }
        return self.client.post(url, data, format="json")

    def test_copy_and_sent_message_are_identical(self):
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self._schedule()
        self.assertEqual(response.status_code, 204)
        message = models.ScheduledMessage.objects.get()
        self.assertTrue(message.message_id)
        copy = push_mail.call_args.args[1]
        self.assertEqual(copy["Message-ID"], message.message_id)
        self.assertIn(constants.CUSTOM_HEADER_SCHEDULED_ID, copy)

        with mock.patch.object(
            models.ScheduledMessage, "delete_imap_copy", return_value=True
        ):
            self.assertTrue(sendmail.send_scheduled_message(message))
        sent = mail.outbox[0].message()
        self.assertEqual(sent["Message-ID"], message.message_id)
        self.assertEqual(sent["Date"], copy["Date"])
        # The headers identifying the copy don't reach the recipients
        self.assertNotIn(constants.CUSTOM_HEADER_SCHEDULED_ID, sent)
        self.assertNotIn(constants.CUSTOM_HEADER_SCHEDULED_DATETIME, sent)

    def test_message_scheduled_before_upgrade(self):
        """Messages without recorded Message-ID can still be sent."""
        message = factories.ScheduledMessageFactory(
            account=self.user,
            sender=self.user.email,
            scheduled_datetime=timezone.now(),
        )
        self.assertEqual(message.message_id, "")
        with mock.patch.object(
            models.ScheduledMessage, "delete_imap_copy", return_value=True
        ):
            self.assertTrue(sendmail.send_scheduled_message(message))
        self.assertTrue(mail.outbox[0].message()["Message-ID"])
