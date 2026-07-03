"""Tests for crypto utility functions."""

from cryptography.fernet import InvalidToken

from django.test import SimpleTestCase
from django.test.utils import override_settings

from modoboa.lib import cryptutils


@override_settings(
    SECRET_KEY="!8o(-dbbl3e+*bh7nx-^xysdt)1gso*%@4ze4-9_9o+i&amp" ";t--u_"
)
class CryptUtilsTest(SimpleTestCase):
    """Tests for modoboa.lib.cryptutils"""

    def test_valid_secret_key_generated(self):
        """Generate a 32 byte key"""
        secret_key = cryptutils.random_key(32)
        self.assertEqual(len(secret_key), 32)

    def test_encrypt(self):
        """Encrypt a string"""
        value = "test"
        expected_output = "test"
        output = cryptutils.encrypt(value)
        output = cryptutils.decrypt(output)
        self.assertEqual(output, expected_output)

    def test_decrypt(self):
        """Decrypt a string encrypted with the legacy key derivation."""
        value = (
            "gAAAAABaXSWk4Via-aYP7diek9MmfknUiEY8szrgxIytdXrbfc"
            "YlbOYiNG01zqkn3a06P1xPXe5XD2SP4UrIvCWzhLs-FO19Cw=="
        )
        expected_output = "test"
        output = cryptutils.decrypt(value)
        self.assertEqual(output, expected_output)

    def test_purpose_key_separation(self):
        """A token encrypted for a purpose must not decrypt for another."""
        token = cryptutils.encrypt("test", purpose="purpose-a")
        self.assertEqual(cryptutils.decrypt(token, purpose="purpose-a"), "test")
        with self.assertRaises(InvalidToken):
            cryptutils.decrypt(token, purpose="purpose-b")

    def test_dedicated_encryption_key(self):
        """MODOBOA_ENCRYPTION_KEY must take precedence over SECRET_KEY."""
        token = cryptutils.encrypt("test")
        with override_settings(MODOBOA_ENCRYPTION_KEY="x" * 64):
            token2 = cryptutils.encrypt("test")
            self.assertEqual(cryptutils.decrypt(token2), "test")
            # Data encrypted with the SECRET_KEY-derived key must not
            # decrypt anymore (and the legacy fallback must not match).
            with self.assertRaises(InvalidToken):
                cryptutils.decrypt(token)
        self.assertEqual(cryptutils.decrypt(token), "test")
