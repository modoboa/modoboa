"""Tests for IMAP argument validation (command injection protection)."""

from unittest import mock

from django.test import SimpleTestCase

from modoboa.webmail.exceptions import ImapError
from modoboa.webmail.lib import imaputils

CRLF_PAYLOAD = "1\r\nA999 UID STORE 1 +FLAGS (\\Deleted)"


class ValidateImapUidTestCase(SimpleTestCase):
    """Tests for validate_imap_uid."""

    def test_valid_uids(self):
        self.assertEqual(imaputils.validate_imap_uid("123"), "123")
        self.assertEqual(imaputils.validate_imap_uid("1,2,3"), "1,2,3")
        self.assertEqual(imaputils.validate_imap_uid(133872), "133872")

    def test_invalid_uids(self):
        for value in [CRLF_PAYLOAD, "1 2", "1;2", "abc", "", None, "1\n2"]:
            with self.assertRaises(ImapError):
                imaputils.validate_imap_uid(value)


class ValidateImapPartnumTestCase(SimpleTestCase):
    """Tests for validate_imap_partnum."""

    def test_valid_partnums(self):
        self.assertEqual(imaputils.validate_imap_partnum("1"), "1")
        self.assertEqual(imaputils.validate_imap_partnum("2.1.3"), "2.1.3")

    def test_invalid_partnums(self):
        for value in ["1] BODY[]", "1\r\nA STORE", "", None, "a.b"]:
            with self.assertRaises(ImapError):
                imaputils.validate_imap_partnum(value)


class EscapeSearchPatternTestCase(SimpleTestCase):
    """Tests for escape_search_pattern."""

    def test_plain_pattern_unchanged(self):
        self.assertEqual(imaputils.escape_search_pattern("hello"), "hello")

    def test_quote_and_backslash_escaped(self):
        # A double quote would otherwise break out of the IMAP quoted string.
        self.assertEqual(imaputils.escape_search_pattern('a"b'), 'a\\"b')
        self.assertEqual(imaputils.escape_search_pattern("a\\b"), "a\\\\b")

    def test_control_characters_rejected(self):
        for value in ["a\r\nb", "a\tb", "a\x00b", "a\x7fb"]:
            with self.assertRaises(ImapError):
                imaputils.escape_search_pattern(value)


class QuoteMailboxNameTestCase(SimpleTestCase):
    """Tests for quote_mailbox_name."""

    def test_plain_name(self):
        self.assertEqual(imaputils.quote_mailbox_name("Sent"), b'"Sent"')
        self.assertEqual(imaputils.quote_mailbox_name("A/B"), b'"A/B"')

    def test_non_ascii_name(self):
        self.assertEqual(imaputils.quote_mailbox_name("Envoyés"), b'"Envoy&AOk-s"')

    def test_quote_and_backslash_escaped(self):
        # A double quote would otherwise break out of the quoted string.
        self.assertEqual(
            imaputils.quote_mailbox_name('INBOX" (MESSAGES'),
            b'"INBOX\\" (MESSAGES"',
        )
        self.assertEqual(imaputils.quote_mailbox_name("a\\b"), b'"a\\\\b"')

    def test_control_characters_rejected(self):
        for value in ["INBOX\r\nA1 DELETE Trash", "a\x00b", "a\tb", "a\x7fb"]:
            with self.assertRaises(ImapError):
                imaputils.quote_mailbox_name(value)


class FetchPartsTestCase(SimpleTestCase):
    """Several parts of a message are retrieved with one command."""

    def _connector(self, response):
        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.m = mock.Mock()
        connector.m.uid.return_value = ("OK", response)
        connector.select_mailbox = mock.Mock()
        return connector

    def test_single_fetch(self):
        connector = self._connector(
            [
                (b"1 (UID 7 BODY[1] {5}", b"hello"),
                (b" BODY[2] {5}", b"world"),
                b")",
            ]
        )
        parts = connector.fetch_parts("7", "INBOX", ["1", "2", "3"])
        connector.m.uid.assert_called_once_with(
            "FETCH", "7", "(BODY.PEEK[1] BODY.PEEK[2] BODY.PEEK[3])"
        )
        # The part the server didn't return is missing
        self.assertEqual(parts, {"1": "hello", "2": "world"})

    def test_nothing_to_fetch(self):
        connector = self._connector([])
        self.assertEqual(connector.fetch_parts("7", "INBOX", []), {})
        connector.m.uid.assert_not_called()

    def test_invalid_partnum(self):
        connector = self._connector([])
        with self.assertRaises(ImapError):
            connector.fetch_parts("7", "INBOX", ["1)\r\nA1 LOGOUT"])


class MailboxStateTestCase(SimpleTestCase):
    """The state summarizes the mailbox content from one STATUS reply."""

    def _connector(self, reply, capabilities):
        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.capabilities = capabilities
        connector._cmd = mock.Mock(return_value=[reply])
        return connector

    def test_state(self):
        connector = self._connector(
            b'"A (b) c" (MESSAGES 3 UIDNEXT 12 UIDVALIDITY 99 UNSEEN 1)', []
        )
        result = connector.mailbox_state("A (b) c")
        self.assertEqual(result, {"state": "3-12-99-1", "unseen": 1})
        self.assertEqual(
            connector._cmd.call_args[0][2], "(MESSAGES UIDNEXT UIDVALIDITY UNSEEN)"
        )

    def test_flag_changes_with_condstore(self):
        connector = self._connector(
            b"INBOX (MESSAGES 3 UIDNEXT 12 UIDVALIDITY 99 UNSEEN 0 "
            b"HIGHESTMODSEQ 1234)",
            ["CONDSTORE"],
        )
        result = connector.mailbox_state("INBOX")
        self.assertEqual(result, {"state": "3-12-99-0-1234", "unseen": 0})
