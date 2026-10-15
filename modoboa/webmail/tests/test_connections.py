"""Tests for the closing of IMAP connections."""

from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import imapemail, imaputils
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


class QuietLogoutTestCase(SimpleTestCase):
    """Closing a connection the server already dropped stays silent."""

    def _connector(self, imap):
        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.m = imap
        return connector

    def test_logout_on_a_broken_connection(self):
        imap = mock.Mock()
        imap._simple_command.side_effect = OSError("connection reset")
        imap.uid.side_effect = OSError("connection reset")
        connector = self._connector(imap)

        connector.logout()

        self.assertIsNone(connector.m)
        imap.shutdown.assert_called_once()

    def test_logout_closes_the_socket_even_if_shutdown_fails(self):
        imap = mock.Mock()
        imap._simple_command.return_value = ("OK", None)
        imap.untagged_responses = {}
        imap.shutdown.side_effect = OSError("already closed")
        connector = self._connector(imap)

        connector.logout()

        self.assertIsNone(connector.m)

    def test_logout_twice(self):
        imap = mock.Mock()
        imap._simple_command.return_value = ("OK", None)
        imap.untagged_responses = {}
        connector = self._connector(imap)
        connector.logout()
        # A second logout (pool eviction after an explicit close...) is a
        # no-op instead of an AttributeError on the dropped connection.
        connector.logout()
        self.assertIsNone(connector.m)

    def test_del_never_raises(self):
        email = imapemail.ImapEmail.__new__(imapemail.ImapEmail)
        email.imapc = mock.Mock()
        email.imapc.__exit__ = mock.Mock(side_effect=imaputils.ImapError("boom"))

        # __del__ is called by the garbage collector, which would only
        # print the exception: call it directly to catch a regression.
        email.__del__()


class TimeoutTestCase(WebmailTestCase):
    """A server that never answers must not block the worker forever."""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_connection_uses_default_timeout(self):
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.mock_imap4.call_args.kwargs["timeout"],
            imaputils.DEFAULT_IMAP_TIMEOUT,
        )

    def test_connection_timeout_is_configurable(self):
        url = reverse("v2:webmail-email-list")
        with self.settings(WEBMAIL_IMAP_TIMEOUT=5):
            response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.mock_imap4.call_args.kwargs["timeout"], 5)

    def test_secured_connection_uses_timeout(self):
        self.set_global_parameter("imap_secured", True)
        url = reverse("v2:webmail-email-list")
        with mock.patch("imaplib.IMAP4_SSL") as mock_imap4_ssl:
            mock_imap4_ssl.return_value = IMAP4Mock()
            with self.settings(WEBMAIL_IMAP_TIMEOUT=5):
                response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.mock_imap4.assert_not_called()
        self.assertEqual(mock_imap4_ssl.call_args.kwargs["timeout"], 5)

    def test_timeout_during_command_is_an_imap_error(self):
        self.mock_imap4.return_value._simple_command = mock.Mock(
            side_effect=TimeoutError("timed out")
        )
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 500)

    def test_timeout_during_uid_command_is_an_imap_error(self):
        self.mock_imap4.return_value.uid = mock.Mock(
            side_effect=TimeoutError("timed out")
        )
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 500)


class ServerInfoCacheTestCase(WebmailTestCase):
    """What the server says about itself is asked once, not on every request."""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def _request(self):
        imap = RecordingIMAP4Mock()
        self.mock_imap4.return_value = imap
        url = reverse("v2:webmail-mailbox-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hdelimiter"], "/")
        return imap.commands

    def test_namespaces_and_capabilities_are_cached(self):
        commands = self._request()
        self.assertIn("NAMESPACE", commands)
        self.assertIn("CAPABILITY", commands)
        commands = self._request()
        self.assertNotIn("NAMESPACE", commands)
        self.assertNotIn("CAPABILITY", commands)

    def test_capabilities_sent_with_the_login_are_used(self):
        """They are free, and fresher than the cached ones."""

        class CapabilitiesOnLoginMock(RecordingIMAP4Mock):
            # The webmail authenticates with AUTHENTICATE, or with LOGIN
            # in development mode
            def _simple_command(self, name, *args, **kwargs):
                result = super()._simple_command(name, *args, **kwargs)
                if name in ("AUTHENTICATE", "LOGIN"):
                    self.untagged_responses["CAPABILITY"] = [b"IMAP4rev1 MOVE"]
                return result

        imap = CapabilitiesOnLoginMock()
        self.mock_imap4.return_value = imap
        self.client.get(reverse("v2:webmail-mailbox-list"))
        self.assertNotIn("CAPABILITY", imap.commands)
