"""Tests for the attachments of forwarded messages."""

from django.core import mail
from django.urls import reverse

from modoboa.webmail.lib.attachments import ComposeSessionManager
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

# Mock message with a PDF attachment ("file.pdf")
MESSAGE_WITH_PDF = 3444

# Plain text message without any attachment
PLAIN_MESSAGE = 40
PLAIN_MESSAGE_BODYSTRUCTURE = [
    b'40 (UID 40 BODYSTRUCTURE ("text" "plain" ("charset" "utf-8") NIL NIL '
    b'"7bit" 5 1 NIL NIL NIL NIL)',
    b")",
]


class IMAP4MockPlainMessage(IMAP4Mock):
    """Fake IMAP server also serving a message without attachment."""

    def uid(self, command, *args):
        if command == "FETCH" and int(args[0]) == PLAIN_MESSAGE:
            return "OK", PLAIN_MESSAGE_BODYSTRUCTURE
        return super().uid(command, *args)


class ForwardAttachmentsTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.authenticate()
        self.url = reverse("v2:webmail-compose-session-list")

    def _create_session(self, **data):
        return self.client.post(self.url, data, format="json")

    def test_attachments_are_copied(self):
        response = self._create_session(
            forward_mailbox="INBOX", forward_mailid=MESSAGE_WITH_PDF
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            [att["fname"] for att in response.json()["attachments"]], ["file.pdf"]
        )
        content = ComposeSessionManager(self.user.username).get_content(
            response.json()["uid"]
        )
        # Stored decoded, like the attachments of a draft
        tmpname = content["attachments"][0]["tmpname"]
        with open(f"{self.workdir}/attachments/{tmpname}", "rb") as fp:
            self.assertTrue(fp.read().startswith(b"%PDF-1.4"))

    def test_message_without_attachment(self):
        self.mock_imap4.return_value = IMAP4MockPlainMessage()
        response = self._create_session(
            forward_mailbox="INBOX", forward_mailid=PLAIN_MESSAGE
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["attachments"], [])

    def test_forwarded_attachment_is_sent(self):
        uid = self._create_session(
            forward_mailbox="INBOX", forward_mailid=MESSAGE_WITH_PDF
        ).json()["uid"]
        mail.outbox = []
        response = self.client.post(
            reverse("v2:webmail-compose-session-send", args=[uid]),
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "Fwd: test",
                "body": "See attached",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        filenames = [part.get_filename() for part in mail.outbox[0].attachments]
        self.assertEqual(filenames, ["file.pdf"])

    def test_partial_forward_is_rejected(self):
        response = self._create_session(forward_mailbox="INBOX")
        self.assertEqual(response.status_code, 400)

    def test_draft_and_forward_are_exclusive(self):
        response = self._create_session(
            from_draft_message=MESSAGE_WITH_PDF,
            forward_mailbox="INBOX",
            forward_mailid=MESSAGE_WITH_PDF,
        )
        self.assertEqual(response.status_code, 400)

    def test_new_message_has_no_attachment(self):
        response = self._create_session()
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("attachments", response.json())
