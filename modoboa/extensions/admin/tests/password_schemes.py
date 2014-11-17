from django.core.urlresolvers import reverse
from modoboa.core import load_core_settings
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.lib import parameters
from modoboa.extensions.admin import factories


class PasswordSchemesTestCase(ModoTestCase):
    fixtures = ['initial_users.json']

    def setUp(self):
        super(PasswordSchemesTestCase, self).setUp()
        factories.populate_database()
        load_core_settings()

    def _create_account(self):
        values = dict(
            username="tester@test.com", first_name="Tester", last_name="Toto",
            password1="toto", password2="toto", role="SimpleUsers",
            quota_act=True,
            is_active=True, email="tester@test.com", stepid='step2'
        )
        self.ajax_post(
            reverse("admin:account_add"),
            values
        )

    def _test_scheme(self, name, startpattern):
        parameters.save_admin('PASSWORD_SCHEME', name, app='core')
        self._create_account()
        account = User.objects.get(username='tester@test.com')
        self.assertTrue(account.password.startswith(startpattern))
        self.assertTrue(account.check_password('toto'))

    def test_sha512crypt_scheme(self):
        self._test_scheme('sha512crypt', '{SHA512-CRYPT}')

    def test_sha256crypt_scheme(self):
        self._test_scheme('sha256crypt', '{SHA256-CRYPT}')

    def test_md5crypt_scheme(self):
        self._test_scheme('md5crypt', '{MD5-CRYPT}')

    def test_sha256_scheme(self):
        self._test_scheme('sha256', '{SHA256}')

    def test_md5_scheme(self):
        self._test_scheme('md5', '{MD5}')

    def test_crypt(self):
        self._test_scheme('crypt', '{CRYPT}')

    def test_plain(self):
        self._test_scheme('plain', '{PLAIN}')
