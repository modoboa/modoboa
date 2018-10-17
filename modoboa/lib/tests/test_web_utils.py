"""Tests for web_utils."""

from django.test import SimpleTestCase

from .. import web_utils


class TestCase(SimpleTestCase):
    """Test functions."""

    def test_size2integer(self):
        self.assertEqual(web_utils.size2integer("1024"), 1024)
        # Convert to bytes
        self.assertEqual(web_utils.size2integer("1K"), 1024)
        self.assertEqual(web_utils.size2integer("1M"), 1048576)
        self.assertEqual(web_utils.size2integer("1G"), 1073741824)
        # Convert to megabytes
        self.assertEqual(web_utils.size2integer("1K", output_unit="MB"), 0)
        self.assertEqual(web_utils.size2integer("1M", output_unit="MB"), 1)
        self.assertEqual(web_utils.size2integer("1G", output_unit="MB"), 1024)
        # Unsupported unit
        with self.assertRaises(ValueError):
            web_utils.size2integer("1K", output_unit="GB")
