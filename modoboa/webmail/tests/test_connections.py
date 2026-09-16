"""Tests for the closing of IMAP connections."""

from unittest import mock

from django.test import SimpleTestCase

from modoboa.webmail.lib import imapemail, imaputils


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
