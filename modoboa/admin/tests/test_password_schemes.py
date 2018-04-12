# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from .. import factories


class PasswordSchemesTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(PasswordSchemesTestCase, cls).setUpTestData()
        factories.populate_database()

    def _create_account(self):
        values = {
            "username": "tester@test.com", "first_name": "Tester",
            "last_name": "Toto", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "tester@test.com", "stepid": "step2"
        }
        self.ajax_post(
            reverse("admin:account_add"),
            values
        )

    def _test_scheme(self, name, startpattern):
        self.set_global_parameter("password_scheme", name, app="core")
        self._create_account()
        account = User.objects.get(username="tester@test.com")
        self.assertTrue(account.password.startswith(startpattern))
        self.assertTrue(account.check_password("Toto1234"))

    def test_bcrypt_scheme(self):
        self._test_scheme("blfcrypt", "{BLF-CRYPT}")

    def test_sha512crypt_scheme(self):
        self._test_scheme("sha512crypt", "{SHA512-CRYPT}")

    def test_sha256crypt_scheme(self):
        self._test_scheme("sha256crypt", "{SHA256-CRYPT}")

    def test_md5crypt_scheme(self):
        self._test_scheme("md5crypt", "{MD5-CRYPT}")

    def test_sha256_scheme(self):
        self._test_scheme("sha256", "{SHA256}")

    def test_md5_scheme(self):
        self._test_scheme("md5", "{MD5}")

    def test_crypt(self):
        self._test_scheme("crypt", "{CRYPT}")

    def test_plain(self):
        self._test_scheme("plain", "{PLAIN}")
