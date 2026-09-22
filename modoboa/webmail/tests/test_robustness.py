"""Tests for invalid inputs and unexpected server replies."""

import base64

from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import factories
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests import data as tests_data
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class QuotaMock(IMAP4Mock):
    """Server answering a given quota definition."""

    def __init__(self, quotadef: bytes, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quotadef = quotadef

    def _simple_command(self, name, *args, **kwargs):
        if name == "GETQUOTAROOT":
            self.untagged_responses["QUOTAROOT"] = [b'"INBOX" "User quota"']
            self.untagged_responses["QUOTA"] = [self.quotadef]
            return "OK", None
        return super()._simple_command(name, *args, **kwargs)


class TextPartMock(IMAP4Mock):
    """Server returning the text part of the message with a PDF."""

    def uid(self, command, *args):
        if command == "FETCH" and "BODY[1]" in args[1]:
            header, payload = tests_data.BODYSTRUCTURE_WITH_PDF[0]
            return "OK", [
                (header.replace(b"BODY[2]", b"BODY[1]"), payload),
                b")",
            ]
        return super().uid(command, *args)


# Message without a Date: header (UID 46936)
_HEADERS_WITHOUT_DATE = (
    b"From: <sender@example.test>\r\n"
    b"To: <user@test.com>\r\n"
    b"Subject: No date\r\n\r\n"
)


class NoDateMock(IMAP4Mock):
    """Server returning a message without a Date: header."""

    def uid(self, command, *args):
        if command == "FETCH" and int(args[0]) == 46936:
            header = b"855 (UID 46936 " + tests_data.BODYSTRUCTURE_4
            if "HEADER.FIELDS" in args[1]:
                return "OK", [
                    (
                        header
                        + b" BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT)] {%d}"
                        % len(_HEADERS_WITHOUT_DATE),
                        _HEADERS_WITHOUT_DATE,
                    ),
                    b")",
                ]
            if args[1] == "(BODYSTRUCTURE)":
                return "OK", [header, ")"]
            return "OK", [
                (b"855 (UID 46936 BODY[1.1] {25}", b"This is a test message.\r\n"),
                b")",
            ]
        return super().uid(command, *args)


class RobustnessTestCase(WebmailTestCase):

    def test_email_without_date(self):
        self.mock_imap4.return_value = NoDateMock()
        self.authenticate()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46936")
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["date"], "")
        self.assertEqual(content["subject"], "No date")

    def _get_quota(self, quotadef: bytes) -> dict:
        self.mock_imap4.return_value = QuotaMock(quotadef)
        self.authenticate()
        response = self.client.get(
            f"{reverse('v2:webmail-mailbox-quota')}?mailbox=INBOX"
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_quota(self):
        quota = self._get_quota(b'"User quota" (STORAGE 25 100 MESSAGE 3 1000)')
        self.assertEqual(quota, {"usage": 25, "current": 25, "limit": 100})

    def test_quota_with_zero_limit(self):
        quota = self._get_quota(b'"User quota" (STORAGE 25 0)')
        self.assertEqual(quota, {"usage": -1, "current": 25, "limit": 0})

    def test_quota_without_storage(self):
        with self.assertLogs("modoboa.webmail", level="WARNING"):
            quota = self._get_quota(b'"User quota" (MESSAGE 3 1000)')
        self.assertEqual(quota, {"usage": -1, "current": None, "limit": None})

    def test_invalid_page_number(self):
        self.authenticate()
        url = reverse("v2:webmail-email-list")
        for page in ("abc", "-1", "1.5"):
            response = self.client.get(f"{url}?page={page}")
            self.assertEqual(response.status_code, 400, page)
        response = self.client.get(f"{url}?page=1")
        self.assertEqual(response.status_code, 200)

    def test_attachment_content_length(self):
        self.authenticate()
        url = reverse("v2:webmail-email-attachment")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=3444&partnum=2")
        self.assertEqual(response.status_code, 200)
        content = base64.b64decode(tests_data.BODYSTRUCTURE_WITH_PDF[0][1])
        self.assertEqual(response.content, content)
        self.assertEqual(response.headers["Content-Length"], str(len(content)))
        self.assertNotIn("Content-Transfer-Encoding", response.headers)

    def test_part_which_is_not_an_attachment(self):
        self.mock_imap4.return_value = TextPartMock()
        self.authenticate()
        url = reverse("v2:webmail-email-attachment")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=3444&partnum=1")
        self.assertEqual(response.status_code, 404)

    def test_scheduled_message_str(self):
        message = factories.ScheduledMessageFactory(
            account=self.user,
            sender="user@test.com",
            subject="Hello",
            scheduled_datetime=timezone.now(),
        )
        self.assertIn("Hello - user@test.com", str(message))
