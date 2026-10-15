from django.test import SimpleTestCase

from modoboa.amavis.utils import fix_utf8_encoding


class FixUTF8EncodingTests(SimpleTestCase):
    """Tests for modoboa_amavis.utils.fix_utf8_encoding()."""

    def test_4_byte_unicode(self):
        value = "\xf0\x9f\x99\x88"
        expected_output = "\U0001f648"  # == See No Evil Moneky
        output = fix_utf8_encoding(value)
        self.assertEqual(output, expected_output)

    def test_truncated_4_byte_unicode(self):
        value = "\xf0\x9f\x99"
        expected_output = "\xf0\x9f\x99"
        output = fix_utf8_encoding(value)
        self.assertEqual(output, expected_output)

    def test_valid_unicode_is_unchanged(self):
        value = "Łukasz Jabłoński"
        output = fix_utf8_encoding(value)
        self.assertEqual(output, value)

    def test_latin1_mojibake_is_repaired(self):
        value = "Å\x81ukasz JabÅ\x82oÅ\x84ski"
        expected_output = "Łukasz Jabłoński"
        output = fix_utf8_encoding(value)
        self.assertEqual(output, expected_output)
