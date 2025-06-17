from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase
from .. import factories


class PasswordSchemesTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def _create_account(self):
        values = {
            "username": "tester@test.com",
            "first_name": "Tester",
            "last_name": "Toto",
            "password": "Toto1234",
            "role": "SimpleUsers",
            "is_active": True,
            "email": "tester@test.com",
            "mailbox": {"use_domain_quota": True},
        }
        response = self.client.post(reverse("v2:account-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

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

    def test_plain(self):
        self._test_scheme("plain", "{PLAIN}")
