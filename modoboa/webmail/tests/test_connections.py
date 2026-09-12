"""Tests for the IMAP connection lifetime (one per request)."""

from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import imaputils
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class RecordingIMAP4Mock(IMAP4Mock):
    """Fake IMAP4 client recording the commands it receives."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = []

    def _simple_command(self, name, *args, **kwargs):
        self.commands.append(name)
        return super()._simple_command(name, *args, **kwargs)


class ConnectorReuseTestCase(SimpleTestCase):
    """A connector is shared, and nested blocks don't close it early."""

    def _connector(self):
        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector._usage_count = 0
        connector.managed = False
        connector.with_namespaces = False
        connector.user = "user@test.com"
        connector.password = "token"
        connector.login = mock.Mock()
        connector.logout = mock.Mock()
        return connector

    def test_nested_blocks_login_once(self):
        connector = self._connector()
        with connector:
            with connector:
                pass
            connector.logout.assert_not_called()
        connector.login.assert_called_once()
        connector.logout.assert_called_once()

    def test_managed_connector_stays_open(self):
        connector = self._connector()
        connector.managed = True
        with connector:
            pass
        connector.login.assert_called_once()
        # Closed with the request, not at the end of the block
        connector.logout.assert_not_called()


class RequestConnectionTestCase(WebmailTestCase):
    """One connection per request, closed when the request ends."""

    def setUp(self):
        super().setUp()
        self.imap = RecordingIMAP4Mock()
        self.mock_imap4.return_value = self.imap
        self.authenticate()

    def test_list_opens_a_single_connection(self):
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mock_imap4.call_count, 1)
        self.assertEqual(self.imap.commands.count("LOGOUT"), 1)

    def test_message_view_opens_a_single_connection(self):
        url = reverse("v2:webmail-email-content")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=46931")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mock_imap4.call_count, 1)
        self.assertEqual(self.imap.commands.count("LOGOUT"), 1)

    def test_sending_opens_a_single_connection(self):
        """Sent copy, draft removal and flagging share one connection."""
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        self.mock_imap4.reset_mock()
        self.imap.commands.clear()
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        response = self.client.post(
            url,
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "test",
                "body": "Test",
                "mailid": 11,
                "original_mailbox": "INBOX",
                "original_mailid": 46931,
                "original_action": "reply",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.mock_imap4.call_count, 1)
        self.assertEqual(self.imap.commands.count("LOGOUT"), 1)

    def test_connection_closed_even_on_error(self):
        url = reverse("v2:webmail-email-content")
        with mock.patch(
            "modoboa.webmail.lib.imaputils.IMAPconnector.fetchmail",
            side_effect=imaputils.ImapError("boom"),
        ):
            response = self.client.get(f"{url}?mailbox=INBOX&mailid=46931")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.imap.commands.count("LOGOUT"), 1)
