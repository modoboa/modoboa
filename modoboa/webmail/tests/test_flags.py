"""Tests for the \\Answered and $Forwarded flags set after sending."""

from unittest import mock

from django.core import mail
from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.exceptions import ImapError
from modoboa.webmail.lib.imaputils import IMAPconnector
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

ADD_FLAG = "modoboa.webmail.lib.imaputils.IMAPconnector._add_flag"


class FlagMethodsTestCase(SimpleTestCase):

    def test_uid_is_passed_as_a_list(self):
        """A plain string would be joined as "1,2,3" and flag other messages."""
        imapc = IMAPconnector.__new__(IMAPconnector)
        imapc._add_flag = mock.Mock()
        imapc.msg_answered("INBOX", "123")
        imapc._add_flag.assert_called_once_with("INBOX", ["123"], r"(\Answered)")
        imapc._add_flag.reset_mock()
        imapc.msg_forwarded("INBOX", "123")
        imapc._add_flag.assert_called_once_with("INBOX", ["123"], "($Forwarded)")


class FlagAfterSendingTestCase(WebmailTestCase):

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
            "subject": "Re: test",
            "body": "Test",
            **extra,
        }
        return self.client.post(url, data, format="json")

    def test_reply_flags_original_as_answered(self):
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._send(
                original_mailbox="INBOX", original_mailid=46931, original_action="reply"
            )
        self.assertEqual(response.status_code, 204)
        add_flag.assert_called_once_with("INBOX", ["46931"], r"(\Answered)")

    def test_forward_flags_original_as_forwarded(self):
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._send(
                original_mailbox="Archive",
                original_mailid=12,
                original_action="forward",
            )
        self.assertEqual(response.status_code, 204)
        add_flag.assert_called_once_with("Archive", ["12"], "($Forwarded)")

    def test_new_message_flags_nothing(self):
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._send()
        self.assertEqual(response.status_code, 204)
        add_flag.assert_not_called()

    def test_partial_original_message_is_rejected(self):
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._send(original_mailbox="INBOX", original_mailid=46931)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)
        add_flag.assert_not_called()

    def test_invalid_action_is_rejected(self):
        response = self._send(
            original_mailbox="INBOX", original_mailid=46931, original_action="delete"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("original_action", response.json())

    def test_flag_failure_does_not_fail_sending(self):
        """The message is sent: failing to flag the original is not an error."""
        with mock.patch(ADD_FLAG, side_effect=ImapError("NO")):
            response = self._send(
                original_mailbox="INBOX", original_mailid=46931, original_action="reply"
            )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
