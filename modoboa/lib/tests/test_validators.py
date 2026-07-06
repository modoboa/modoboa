"""Tests for validators."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .. import validators


class HostnameValidatorTestCase(SimpleTestCase):
    """Test the hostname validator."""

    def test_accepts_valid_hostnames(self):
        for value in ["example.com", "sub.example.com", "example.com.", "localhost"]:
            validators.validate_hostname(value)  # must not raise

    def test_rejects_trailing_garbage(self):
        """An unanchored match used to accept trailing content.

        Values such as "good.com\\nevil" flowed into the Postfix relay
        next_hop and other map/config sinks.
        """
        for value in [
            "good.com\nevil",
            "good.com\nvictim.com relay:[evil]:25",
            "good.com x",
            "good.com;evil",
            "good.com\r",
            "",
        ]:
            with self.assertRaises(
                ValidationError, msg=f"{value!r} should be rejected"
            ):
                validators.validate_hostname(value)
