# -*- coding: utf-8 -*-

"""Tests for crypto utility functions."""

from __future__ import unicode_literals

from django.test import SimpleTestCase
from django.test.utils import override_settings

from modoboa.lib import cryptutils


@override_settings(SECRET_KEY="!8o(-dbbl3e+*bh7nx-^xysdt)1gso*%@4ze4-9_9o+i&amp"
                              ";t--u_")
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
        """Decrypt a string"""
        value = "gAAAAABaXSWk4Via-aYP7diek9MmfknUiEY8szrgxIytdXrbfc"\
                "YlbOYiNG01zqkn3a06P1xPXe5XD2SP4UrIvCWzhLs-FO19Cw=="
        expected_output = "test"
        output = cryptutils.decrypt(value)
        self.assertEqual(output, expected_output)
