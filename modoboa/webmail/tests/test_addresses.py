"""Tests for address lists whose display names contain commas (#2347)."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import imapheader
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests import data as tests_data
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

OUTLOOK_NAME = "Berhane, Kidane T - Eagan, MN"

# Message from an Outlook sender, as described in #2347 (UID 46935)
_HEADERS = (
    f'From: "{OUTLOOK_NAME}" <kidane@example.test>\r\n'
    'To: <user@test.com>, "Doe, Jane" <jane@example.test>\r\n'
    "Cc: =?utf-8?q?Doe=2C_John?= <john@example.test>, other@example.test\r\n"
    "Subject: Comma test\r\n"
    "Date: Wed, 28 Dec 2011 13:29:17 +0100\r\n"
    f'Reply-To: "{OUTLOOK_NAME}" <kidane@example.test>\r\n'
    "Message-ID: <comma-test@example.test>\r\n\r\n"
).encode()

HEADERS_RESPONSE = [
    (
        b"855 (UID 46935 "
        + tests_data.BODYSTRUCTURE_4
        + b" BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT REPLY-TO MESSAGE-ID)] {%d}"
        % len(_HEADERS),
        _HEADERS,
    ),
    b")",
]
BODYSTRUCTURE_RESPONSE = [(b"855 (UID 46935 " + tests_data.BODYSTRUCTURE_4), ")"]
BODY_RESPONSE = [
    (b"855 (UID 46935 BODY[1.1] {25}", b"This is a test message.\r\n"),
    b")",
]


class IMAP4MockOutlookSender(IMAP4Mock):
    """Fake IMAP server serving the message of #2347."""

    def uid(self, command, *args):
        if command == "FETCH" and int(args[0]) == 46935:
            if args[1] == "(BODYSTRUCTURE)":
                return "OK", BODYSTRUCTURE_RESPONSE
            if "HEADER.FIELDS" in args[1]:
                return "OK", HEADERS_RESPONSE
            return "OK", BODY_RESPONSE
        return super().uid(command, *args)


class ParseAddressListTestCase(SimpleTestCase):

    def test_quoted_name_with_commas(self):
        result = imapheader.parse_address_list(
            f'"{OUTLOOK_NAME}" <kidane@example.test>, jane@example.test'
        )
        self.assertEqual(
            [addr["address"] for addr in result],
            ["kidane@example.test", "jane@example.test"],
        )
        self.assertEqual(result[0]["name"], OUTLOOK_NAME)

    def test_encoded_name_with_comma(self):
        result = imapheader.parse_address_list(
            "=?utf-8?q?Doe=2C_John?= <john@example.test>"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["address"], "john@example.test")
        self.assertEqual(result[0]["name"], "Doe, John")

    def test_non_ascii_name(self):
        result = imapheader.parse_address_list(
            "=?utf-8?q?Ren=C3=A9?= <rene@example.test>"
        )
        self.assertEqual(result[0]["name"], "René")

    def test_folded_header(self):
        result = imapheader.parse_address_list("a@example.test,\r\n b@example.test")
        self.assertEqual(
            [addr["address"] for addr in result], ["a@example.test", "b@example.test"]
        )

    def test_empty(self):
        self.assertEqual(imapheader.parse_address_list(""), [])


class ReplyToOutlookSenderTestCase(WebmailTestCase):
    """Replying to a sender whose name contains commas (#2347)."""

    def test_reply_keeps_addresses_whole(self):
        self.mock_imap4.return_value = IMAP4MockOutlookSender()
        self.authenticate()
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46935&context=reply")
        self.assertEqual(response.status_code, 200)
        content = response.json()

        self.assertEqual(content["from_address"]["address"], "kidane@example.test")
        self.assertEqual(content["from_address"]["name"], OUTLOOK_NAME)
        self.assertEqual(
            [(rcpt["address"], rcpt.get("name")) for rcpt in content["reply_to"]],
            [("kidane@example.test", OUTLOOK_NAME)],
        )
        self.assertEqual(
            [(rcpt["address"], rcpt.get("name")) for rcpt in content["to"]],
            [("user@test.com", None), ("jane@example.test", "Doe, Jane")],
        )
        # Encoded display name: the comma only appears once decoded
        self.assertEqual(
            [(rcpt["address"], rcpt.get("name")) for rcpt in content["cc"]],
            [("john@example.test", "Doe, John"), ("other@example.test", None)],
        )
