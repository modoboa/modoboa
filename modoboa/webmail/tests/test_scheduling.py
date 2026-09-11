"""Tests for SMTP error handling and scheduled messages recovery."""

import smtplib
from unittest import mock

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import constants, factories, jobs
from modoboa.webmail.exceptions import WebmailInternalError
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

GET_CONNECTION = "modoboa.webmail.lib.sendmail.mail.get_connection"
SCHEDULED = constants.SchedulingState.SCHEDULED.value
SENDING = constants.SchedulingState.SENDING.value
SEND_ERROR = constants.SchedulingState.SEND_ERROR.value


class SendMailErrorsTestCase(WebmailTestCase):
    """Errors while sending a message directly."""

    def _send(self):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        return self.client.post(
            url,
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "test",
                "body": "Test",
            },
            format="json",
        )

    def test_connection_refused(self):
        self.authenticate()
        with mock.patch(
            GET_CONNECTION, side_effect=ConnectionRefusedError("Connection refused")
        ):
            response = self._send()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Connection refused")

    def test_server_disconnected(self):
        self.authenticate()
        with mock.patch(
            GET_CONNECTION,
            side_effect=smtplib.SMTPServerDisconnected(
                "Connection unexpectedly closed"
            ),
        ):
            response = self._send()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Connection unexpectedly closed")

    def test_smtp_error_is_decoded(self):
        self.authenticate()
        with mock.patch(
            GET_CONNECTION,
            side_effect=smtplib.SMTPSenderRefused(553, b"Sender refused", "a@b.c"),
        ):
            response = self._send()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Sender refused")

    def test_sent_copy_failure_is_not_an_error(self):
        """The message is sent: a failing Sent copy must not report an error."""
        self.authenticate()
        mail.outbox = []
        with mock.patch(
            "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail",
            side_effect=WebmailInternalError("Mailbox does not exist"),
        ):
            response = self._send()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)


class ScheduledMessageRecoveryTestCase(WebmailTestCase):
    """Scheduled messages must never stay stuck in the SENDING state."""

    def _message(self, **kwargs):
        kwargs.setdefault("scheduled_datetime", timezone.now())
        return factories.ScheduledMessageFactory(
            account=self.user, sender=self.user.email, **kwargs
        )

    def test_network_error_flags_message(self):
        message = self._message(status=SENDING)
        with mock.patch(GET_CONNECTION, side_effect=OSError("Network is unreachable")):
            jobs.send_scheduled_message(message.id)
        message.refresh_from_db()
        self.assertEqual(message.status, SEND_ERROR)
        self.assertEqual(message.error, "Network is unreachable")

    def test_long_error_is_truncated(self):
        message = self._message(status=SENDING)
        with mock.patch(GET_CONNECTION, side_effect=OSError("x" * 400)):
            jobs.send_scheduled_message(message.id)
        message.refresh_from_db()
        self.assertEqual(message.status, SEND_ERROR)
        self.assertEqual(len(message.error), 255)

    def test_unexpected_error_flags_message(self):
        message = self._message(status=SENDING)
        with mock.patch(
            "modoboa.webmail.lib.sendmail.send_scheduled_message",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                jobs.send_scheduled_message(message.id)
        message.refresh_from_db()
        self.assertEqual(message.status, SEND_ERROR)
        self.assertTrue(message.error)

    def test_cancelled_message_is_ignored(self):
        # The message was deleted while its job was waiting in the queue
        jobs.send_scheduled_message(999999)

    def test_stale_sending_message_is_flagged(self):
        now = timezone.now()
        stale = self._message(
            status=SENDING, scheduled_datetime=now - relativedelta(hours=2)
        )
        recent = self._message(
            status=SENDING, scheduled_datetime=now - relativedelta(minutes=5)
        )
        with mock.patch("django_rq.get_queue"):
            jobs.send_scheduled_messages()
        stale.refresh_from_db()
        recent.refresh_from_db()
        self.assertEqual(stale.status, SEND_ERROR)
        self.assertTrue(stale.error)
        self.assertEqual(recent.status, SENDING)

        # The job of the interrupted message, if it runs later, does nothing
        with mock.patch(GET_CONNECTION) as get_connection:
            jobs.send_scheduled_message(stale.id)
        get_connection.assert_not_called()

    def test_reschedule_failed_message(self):
        self.authenticate()
        message = self._message(
            status=SEND_ERROR, error="Connection refused", imap_uid=10
        )
        url = reverse("v2:webmail-scheduled-message-detail", args=[message.id])
        response = self.client.patch(
            url,
            {"scheduled_datetime": timezone.now() + relativedelta(days=1)},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        message.refresh_from_db()
        self.assertEqual(message.status, SCHEDULED)
        self.assertIsNone(message.error)
