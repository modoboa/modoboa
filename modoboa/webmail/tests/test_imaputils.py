"""Tests for IMAP argument validation (command injection protection)."""

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
