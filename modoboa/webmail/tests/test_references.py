"""Tests for the References header: replies keep the whole thread."""

from unittest import mock

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import models
from modoboa.webmail.lib.utils import build_references
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests import data as tests_data
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"

THREAD_HEADERS = (
    b"From: Sender <sender@example.test>\r\n"
    b"To: <user@test.com>\r\n"
    b"Subject: Re: Thread\r\n"
    b"Date: Wed, 28 Dec 2011 13:29:17 +0100\r\n"
    b"Message-ID: <3@example.test>\r\n"
    b"In-Reply-To: <2@example.test>\r\n"
    b"References: <1@example.test>\r\n <2@example.test>\r\n\r\n"
)


class ThreadMock(IMAP4Mock):
    """Server returning a message which is itself a reply."""

    def uid(self, command, *args):
        if command == "FETCH" and int(args[0]) == 46933 and "HEADER.FIELDS" in args[1]:
            fields = args[1][args[1].index("(", 1) : args[1].index(")") + 1]
            return "OK", [
                (
                    b"855 (UID 46933 "
                    + tests_data.BODYSTRUCTURE_4
                    + f" BODY[HEADER.FIELDS {fields}] {{{len(THREAD_HEADERS)}}}".encode(),
                    THREAD_HEADERS,
                ),
                b")",
            ]
        return super().uid(command, *args)


class ReferencesTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _session(self):
        return self.client.post(reverse("v2:webmail-compose-session-list")).json()[
            "uid"
        ]

    def _data(self, **extra):
        return {
            "sender": self.user.email,
            "to": ["sender@example.test"],
            "subject": "Re: Thread",
            "body": "Hello",
            "in_reply_to": "<3@example.test>",
            "references": "<1@example.test> <2@example.test>",
            **extra,
        }

    def test_build_references(self):
        self.assertEqual(build_references("", "<1@a>"), "<1@a>")
        self.assertEqual(
            build_references("<1@a>\r\n <2@a>", "<3@a>"), "<1@a> <2@a> <3@a>"
        )
        # The parent is not added twice
        self.assertEqual(build_references("<1@a> <2@a>", "<2@a>"), "<1@a> <2@a>")

    def test_reply_content_exposes_references(self):
        self.mock_imap4.return_value = ThreadMock()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46933&context=reply")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message_id"], "<3@example.test>")
        self.assertEqual(
            response.json()["references"], "<1@example.test> <2@example.test>"
        )

    def test_send_keeps_the_thread(self):
        url = reverse("v2:webmail-compose-session-send", args=[self._session()])
        response = self.client.post(url, self._data(), format="json")
        self.assertEqual(response.status_code, 204)
        message = mail.outbox[0].message()
        self.assertEqual(message["In-Reply-To"], "<3@example.test>")
        self.assertEqual(
            message["References"],
            "<1@example.test> <2@example.test> <3@example.test>",
        )

    def test_scheduled_message_keeps_the_thread(self):
        scheduled_datetime = timezone.now() + relativedelta(hours=1)
        url = reverse("v2:webmail-compose-session-send", args=[self._session()])
        response = self.client.post(
            url,
            self._data(scheduled_datetime=scheduled_datetime.isoformat()),
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        message = models.ScheduledMessage.objects.get().to_email_message().message()
        self.assertEqual(
            message["References"],
            "<1@example.test> <2@example.test> <3@example.test>",
        )

    def test_draft_keeps_the_thread(self):
        url = reverse("v2:webmail-compose-session-save", args=[self._session()])
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self.client.post(url, self._data(), format="json")
        self.assertEqual(response.status_code, 200)
        draft = push_mail.call_args.args[1]
        self.assertEqual(draft["In-Reply-To"], "<3@example.test>")
        self.assertIn("<2@example.test> <3@example.test>", draft["References"])

    def test_reopened_draft_exposes_thread(self):
        self.mock_imap4.return_value = ThreadMock()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=Drafts&mailid=46933&context=edit")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["in_reply_to"], "<2@example.test>")
        self.assertEqual(
            response.json()["references"], "<1@example.test> <2@example.test>"
        )
