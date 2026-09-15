"""Tests for the \\Answered and $Forwarded flags set after sending."""

from unittest import mock

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from modoboa.lib import dovecot
from modoboa.webmail import constants, factories, models
from modoboa.webmail.exceptions import ImapError
from modoboa.webmail.lib import sendmail
from modoboa.webmail.lib.imaputils import IMAPconnector
from modoboa.webmail.mocks import IMAP4Mock
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


ADD_MESSAGE_FLAGS = "modoboa.lib.dovecot.DoveadmCmdBackend.add_message_flags"
MOVE_MESSAGE = "modoboa.lib.dovecot.DoveadmCmdBackend.move_message"
PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"

DRAFT_HEADERS = (
    b"From: user@test.com\r\n"
    b"To: sender@example.test\r\n"
    b"Subject: Re: test\r\n"
    b"Date: Tue, 15 Sep 2026 10:00:00 +0200\r\n"
    b"X-Modoboa-Original-Message: reply 46931 Archive/2026 projects\r\n\r\n"
)


class DraftMock(IMAP4Mock):
    """Server holding a reply saved as draft (UID 70)."""

    def uid(self, command, *args):
        if command == "FETCH" and int(args[0]) == 70 and "HEADER.FIELDS" in args[1]:
            fields = args[1][args[1].index("(", 1) : args[1].index(")") + 1]
            item = f" BODY[HEADER.FIELDS {fields}] {{{len(DRAFT_HEADERS)}}}"
            return "OK", [
                (
                    b"1 (UID 70 BODYSTRUCTURE "
                    b'("text" "plain" ("charset" "utf-8") NIL NIL "7bit" 0 0 '
                    b"NIL NIL NIL NIL)" + item.encode(),
                    DRAFT_HEADERS,
                ),
                b")",
            ]
        return super().uid(command, *args)


class FlagLaterTestCase(WebmailTestCase):
    """Flags are also set for scheduled messages and replies saved as draft."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _url(self, action):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        return reverse(f"v2:webmail-compose-session-{action}", args=[uid])

    def _data(self, **extra):
        return {
            "sender": self.user.email,
            "to": ["sender@example.test"],
            "subject": "Re: test",
            "body": "Test",
            "original_mailbox": "Archive/2026 projects",
            "original_mailid": 46931,
            "original_action": "reply",
            **extra,
        }

    def test_draft_remembers_original_message(self):
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self.client.post(self._url("save"), self._data(), format="json")
        self.assertEqual(response.status_code, 200)
        draft = push_mail.call_args.args[1]
        self.assertEqual(
            draft[constants.CUSTOM_HEADER_ORIGINAL_MESSAGE],
            "reply 46931 Archive/2026 projects",
        )

    def test_sent_message_does_not_expose_original_message(self):
        with mock.patch(ADD_FLAG):
            response = self.client.post(self._url("send"), self._data(), format="json")
        self.assertEqual(response.status_code, 204)
        self.assertNotIn(
            constants.CUSTOM_HEADER_ORIGINAL_MESSAGE, mail.outbox[0].message()
        )

    def test_reopened_draft_exposes_original_message(self):
        self.mock_imap4.return_value = DraftMock()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=Drafts&mailid=70&context=edit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["original_message"],
            {
                "original_action": "reply",
                "original_mailid": 46931,
                "original_mailbox": "Archive/2026 projects",
            },
        )

    def test_scheduled_message_flags_original_once_sent(self):
        scheduled_datetime = timezone.now() + relativedelta(hours=1)
        with mock.patch(ADD_FLAG) as add_flag:
            response = self.client.post(
                self._url("send"),
                self._data(scheduled_datetime=scheduled_datetime.isoformat()),
                format="json",
            )
        self.assertEqual(response.status_code, 204)
        # Not sent yet: nothing flagged
        add_flag.assert_not_called()
        message = models.ScheduledMessage.objects.get()

        with (
            mock.patch(ADD_MESSAGE_FLAGS) as add_message_flags,
            mock.patch(MOVE_MESSAGE),
        ):
            self.assertTrue(sendmail.send_scheduled_message(message))
        add_message_flags.assert_called_once_with(
            self.user.email, "Archive/2026 projects", 46931, ["\\Answered"]
        )

    def test_scheduled_flag_failure_does_not_fail_sending(self):
        message = factories.ScheduledMessageFactory(
            account=self.user,
            scheduled_datetime=timezone.now(),
            original_mailbox="INBOX",
            original_mailid=12,
            original_action="forward",
        )
        with (
            mock.patch(
                ADD_MESSAGE_FLAGS, side_effect=dovecot.DoveadmError("error")
            ) as add_message_flags,
            mock.patch(MOVE_MESSAGE),
            self.assertLogs("modoboa.webmail", level="WARNING"),
        ):
            self.assertTrue(sendmail.send_scheduled_message(message))
        add_message_flags.assert_called_once_with(
            self.user.email, "INBOX", 12, ["$Forwarded"]
        )
        self.assertEqual(len(mail.outbox), 1)
