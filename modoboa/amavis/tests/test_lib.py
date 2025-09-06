from django.test import SimpleTestCase

from modoboa.lib.tests import ModoTestCase
from modoboa.amavis.lib import cleanup_email_address, make_query_args


class MakeQueryArgsTests(ModoTestCase):
    """Tests for modoboa_amavis.lib.make_query_args()."""

    def test_simple_email_address_001(self):
        """Check case insensitive email address without recipient delimiter."""
        self.set_global_parameter("localpart_is_case_sensitive", False)
        self.set_global_parameter("recipient_delimiter", "")
        address = "User+Foo@sub.exAMPLE.COM"
        expected_output = [
            "user+foo@sub.example.com",
        ]
        output = make_query_args(address)
        self.assertEqual(output, expected_output)

    def test_simple_email_address_002(self):
        """Check case sensitive email address with recipient delimiter."""
        self.set_global_parameter("localpart_is_case_sensitive", True)
        self.set_global_parameter("recipient_delimiter", "+")
        address = "User+Foo@sub.exAMPLE.COM"
        expected_output = [
            "User+Foo@sub.exAMPLE.COM",
            "User+Foo@sub.example.com",
            "User@sub.example.com",
        ]
        output = make_query_args(address)
        self.assertEqual(output, expected_output)

    def test_simple_email_address_003(self):
        """Check email address with recipient delimiter wildcard."""
        self.set_global_parameter("localpart_is_case_sensitive", False)
        self.set_global_parameter("recipient_delimiter", "+")
        address = "User+Foo@sub.exAMPLE.COM"
        expected_output = [
            "user+foo@sub.example.com",
            "user+.*@sub.example.com",
            "user@sub.example.com",
        ]
        output = make_query_args(address, exact_extension=False, wildcard=".*")
        self.assertEqual(output, expected_output)

    def test_simple_email_address_004(self):
        """Check domain search."""
        self.set_global_parameter("localpart_is_case_sensitive", False)
        self.set_global_parameter("recipient_delimiter", "+")
        address = "User+Foo@sub.exAMPLE.COM"
        expected_output = [
            "user+foo@sub.example.com",
            "user+.*@sub.example.com",
            "user@sub.example.com",
            "@sub.example.com",
            "@.",
        ]
        output = make_query_args(
            address, exact_extension=False, wildcard=".*", domain_search=True
        )
        self.assertEqual(output, expected_output)

    def test_simple_email_address_idn(self):
        """Check email address with international domain name."""
        self.set_global_parameter("localpart_is_case_sensitive", False)
        self.set_global_parameter("recipient_delimiter", "")
        address = "Pingüino@Pájaro.Niño.exAMPLE.COM"
        expected_output = [
            "Pingüino@Pájaro.Niño.exAMPLE.COM",
            "pingüino@xn--pjaro-xqa.xn--nio-8ma.example.com",
        ]
        output = make_query_args(address)
        self.assertEqual(output, expected_output)


class FixUTF8EncodingTests(SimpleTestCase):
    """Tests for modoboa_amavis.lib.cleanup_email_address()."""

    def test_value_with_newline(self):
        value = '"John Smith" <john.smith@example.com>\n'
        expected_output = "John Smith <john.smith@example.com>"
        output = cleanup_email_address(value)
        self.assertEqual(output, expected_output)

    def test_no_name(self):
        value = "<john.smith@example.com>"
        expected_output = "john.smith@example.com"
        output = cleanup_email_address(value)
        self.assertEqual(output, expected_output)
