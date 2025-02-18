import os
import shutil
import tempfile

from django.test.utils import override_settings

from modoboa.core import checks
from modoboa.lib.tests import SimpleModoTestCase


class CheckSessionCookieSecureTest(SimpleModoTestCase):

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workdir)

    @override_settings(USE_TZ=False)
    def test_use_tz_false(self):
        """If USE_TZ is off provide one warning."""
        self.assertEqual(checks.check_use_tz_enabled(None), [checks.W001])

    @override_settings(USE_TZ=True)
    def test_use_tz_true(self):
        """If USE_TZ is on, there's no warning about it."""
        self.assertEqual(checks.check_use_tz_enabled(None), [])

    def test_rsa_private_key_exists(self):
        with override_settings(BASE_DIR=self.workdir):
            os.environ["OIDC_RSA_PRIVATE_KEY"] = "NONE"
            msgs = checks.check_rsa_private_key_exists(None)
            self.assertEqual(len(msgs), 1)
            self.assertTrue(os.path.exists(f"{self.workdir}/.env"))
            os.environ["OIDC_RSA_PRIVATE_KEY"] = "KEY"
            msgs = checks.check_rsa_private_key_exists(None)
            self.assertEqual(len(msgs), 0)

    def test_password_hasher_checks(self):
        msgs = checks.check_password_hasher(None)
        self.assertEqual(msgs, [])
        self.set_global_parameter("password_scheme", "crypt")
        msgs = checks.check_password_hasher(None)
        self.assertEqual(msgs, [checks.W002])
