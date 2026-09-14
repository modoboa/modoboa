"""Tests for unseen counters, fetched with the mailboxes list."""

from django.urls import reverse

from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

LIST_RESPONSES = [
    b'(\\Subscribed \\HasNoChildren) "." "INBOX"',
    b'(\\Subscribed \\UnMarked \\HasNoChildren) "." "Archive"',
    # \\Noselect: cannot be queried with STATUS
    b'(\\Noselect \\HasChildren) "." "Parent"',
]


class RecordingMock(IMAP4Mock):
    """Base mock recording the commands it receives."""

    capability = b"QUOTA"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = []
        self.list_arguments = []

    def _simple_command(self, name, *args, **kwargs):
        self.commands.append(name)
        if name == "CAPABILITY":
            self.untagged_responses["CAPABILITY"] = [self.capability]
            return "OK", None
        if name == "LIST":
            self.list_arguments.append([str(arg) for arg in args])
            self.untagged_responses["LIST"] = list(LIST_RESPONSES)
            self.add_status_responses()
            return "OK", None
        return super()._simple_command(name, *args, **kwargs)

    def add_status_responses(self):
        """Servers without LIST-STATUS send nothing along the LIST reply."""


class ListStatusMock(RecordingMock):
    """Server supporting LIST-STATUS (RFC 5819)."""

    capability = b"QUOTA LIST-STATUS"

    def add_status_responses(self):
        self.untagged_responses["STATUS"] = [
            b'"INBOX" (MESSAGES 12 UNSEEN 10)',
            b'"Archive" (MESSAGES 5 UNSEEN 3)',
        ]


class UnseenCountersTestCase(WebmailTestCase):

    def _get_mailboxes(self, mock):
        self.mock_imap4.return_value = mock
        self.authenticate()
        response = self.client.get(reverse("v2:webmail-mailbox-list"))
        self.assertEqual(response.status_code, 200)
        return {mb["name"]: mb for mb in response.json()["mailboxes"]}

    def test_counters_come_with_the_list(self):
        """One LIST command, no STATUS command per mailbox."""
        mock = ListStatusMock()
        mailboxes = self._get_mailboxes(mock)
        self.assertEqual(mailboxes["INBOX"]["unseen"], 10)
        self.assertEqual(mailboxes["Archive"]["unseen"], 3)
        # \\Noselect mailbox: no counter
        self.assertEqual(mailboxes["Parent"]["unseen"], 0)
        self.assertNotIn("STATUS", mock.commands)
        self.assertEqual(mock.commands.count("LIST"), 1)
        self.assertIn(
            "(SUBSCRIBED CHILDREN STATUS (MESSAGES UNSEEN))", mock.list_arguments[0]
        )

    def test_fallback_without_list_status(self):
        """Without the extension, counters are asked one mailbox at a time."""
        mock = RecordingMock()
        mailboxes = self._get_mailboxes(mock)
        # IMAP4Mock answers 10 unseen messages to every STATUS command
        self.assertEqual(mailboxes["INBOX"]["unseen"], 10)
        self.assertEqual(mailboxes["Archive"]["unseen"], 10)
        self.assertEqual(mailboxes["Parent"]["unseen"], 0)
        self.assertEqual(mock.commands.count("STATUS"), 2)
        self.assertIn("(SUBSCRIBED CHILDREN)", mock.list_arguments[0])
