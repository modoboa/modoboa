"""Tests for IMAP errors raised by mailbox (folder) operations."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.exceptions import MailboxOperationError, WebmailInternalError
from modoboa.webmail.lib.imaputils import IMAP4Error
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class IMAP4MockRefusing(IMAP4Mock):
    """Fake IMAP server refusing every mailbox operation."""

    def create(self, name):
        return "NO", [b"[ALREADYEXISTS] Mailbox already exists"]

    def rename(self, oldname, newname):
        return "NO", [b"[NONEXISTENT] Mailbox doesn't exist: Test"]

    def delete(self, name):
        return "NO", [b"[NONEXISTENT] Mailbox doesn't exist: Test"]

    def subscribe(self, name):
        # imaplib raises on BAD responses instead of returning them
        raise IMAP4Error("SUBSCRIBE command error: BAD [b'Invalid name']")


class WebmailInternalErrorTestCase(SimpleTestCase):

    def test_bytes_reason(self):
        """Server responses are bytes: they must not crash the constructor."""
        error = WebmailInternalError(b"[ALREADYEXISTS] Mailbox already exists")
        self.assertEqual(str(error), "Server response: Mailbox already exists")

    def test_unstructured_reason(self):
        self.assertEqual(str(WebmailInternalError(b"Failure")), "Failure")
        self.assertEqual(str(WebmailInternalError("Failure")), "Failure")

    def test_mailbox_operation_error_is_a_user_error(self):
        self.assertEqual(MailboxOperationError(b"No").http_code, 400)


class MailboxOperationErrorsTestCase(WebmailTestCase):
    """A refused folder operation is reported (400), not a crash (500)."""

    def setUp(self):
        super().setUp()
        self.mock_imap4.return_value = IMAP4MockRefusing()
        self.authenticate()

    def test_create_existing_folder(self):
        url = reverse("v2:webmail-mailbox-list")
        response = self.client.post(url, {"name": "Test"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "Server response: Mailbox already exists"
        )

    def test_rename_unknown_folder(self):
        url = reverse("v2:webmail-mailbox-rename")
        response = self.client.post(
            url, {"name": "Renamed", "oldname": "Test"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"], "Server response: Mailbox doesn't exist: Test"
        )

    def test_delete_unknown_folder(self):
        url = reverse("v2:webmail-mailbox-delete")
        response = self.client.post(url, {"name": "Test"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Mailbox doesn't exist", response.json()["error"])

    def test_bad_response(self):
        url = reverse("v2:webmail-mailbox-subscriptions")
        response = self.client.post(
            url, {"changes": [{"name": "Test", "subscribed": True}]}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("BAD", response.json()["error"])

    def test_invalid_mailbox_name(self):
        """A mailbox name that can't be sent to the server is a bad request."""
        url = reverse("v2:webmail-email-list")
        response = self.client.get(url, {"mailbox": "INBOX\r\nA1 DELETE Trash"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid mailbox name")
