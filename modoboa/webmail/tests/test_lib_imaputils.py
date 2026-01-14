"""mailutils tests"""

import unittest

from modoboa.webmail.lib.imaputils import IMAPconnector


class ImapUtilsTestCase(unittest.TestCase):
    """Test mail utils library"""

    def setUp(self):
        self.imap_connector = IMAPconnector(user="test", password="test")

    def test_criterions_one_criterion_with_pattern(self):
        """Test with Criterion and pattern"""
        self.imap_connector.criterions = []
        self.imap_connector.parse_search_parameters("from_addr", "bob")
        result = [bytearray('(FROM "bob")', "utf8")]
        self.assertEqual(self.imap_connector.criterions, result)

    def test_criterions_both_criterion_with_pattern(self):
        """Test with both Criterion and pattern"""
        self.imap_connector.criterions = []
        self.imap_connector.parse_search_parameters("both", "bob")
        result = [bytearray('OR (FROM "bob") (SUBJECT "bob")', "utf8")]
        self.assertEqual(self.imap_connector.criterions, result)

    def test_criterions_one_criterion_without_pattern(self):
        """Test with Criterion and empty pattern"""
        self.imap_connector.criterions = []
        self.imap_connector.parse_search_parameters("SEEN", "")
        result = [bytearray("ALL", "utf8")]
        self.assertEqual(self.imap_connector.criterions, result)
