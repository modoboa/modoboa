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
