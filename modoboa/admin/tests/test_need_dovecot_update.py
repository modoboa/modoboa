"""Management command tests."""

import os
import shutil
import tempfile

from django.core.management import call_command
from django.urls import reverse

from modoboa.core.tests.test_views import SETTINGS_SAMPLE

from modoboa.lib.tests import ModoTestCase
from .. import factories


class NeedDovecotUpdateTestCase(ModoTestCase):
    """Test need dovecot ldap update command."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def setUp(self):
        """Initiate initial env."""
        super().setUp()
        self.workdir = tempfile.mkdtemp()
        self.localconfig.need_dovecot_update = False
        self.localconfig.save()

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def test_update_dovecot_update_state_valid_form(self):
        url = reverse("core:parameters")
        settings = SETTINGS_SAMPLE.copy()
        response = self.client.post(url, settings, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Parameters saved")
        self.localconfig.refresh_from_db()
        self.assertTrue(self.localconfig.need_dovecot_update)

    def test_update_dovecot_ldap_conf(self):
        self.localconfig.need_dovecot_update = True
        self.localconfig.save()
        self.assertTrue(self.localconfig.need_dovecot_update)

        tmp_file = os.path.join(self.workdir, "test-dovecot-ldap.conf")
        self.set_global_parameters({
            "authentication_type": "ldap",
            "ldap_dovecot_sync": True,
            "ldap_dovecot_conf_file": tmp_file,
            "ldap_server_address": "localhost",
            "ldap_server_port": "636",
            "ldap_enable_secondary_server": True,
            "ldap_secondary_server_address": "localhost2",
            "ldap_secondary_server_port": "636",
            "ldap_secured": "ssl",
            "ldap_bind_dn": "DC=test,DC=lan",
            "ldap_bind_password": "test",
            "ldap_search_base": "CN=Users,DC=test,DC=lan",
            "ldap_search_filter": "(& (objectClass=user) (|(mail=%(user)s)(sAMAccountName=%(user)s)) )"
        }, app="core")

        # Generated file checks
        call_command("update_dovecot_conf")
        self.assertTrue(os.path.exists(tmp_file))

        with open(tmp_file) as tmp:
            content = tmp.read()
        self.assertIn("uris = ldaps://localhost:636 ldaps://localhost2:636", content)
        self.assertIn("dn = \"DC=test,DC=lan\"", content)
        self.assertIn("dnpass = \'test\'", content)
        self.assertIn("base = CN=Users,DC=test,DC=lan", content)
        self.assertIn("user_filter = (& (objectClass=user) (|(mail=%u)(sAMAccountName=%u)) )", content)
        self.assertIn("pass_filter = (& (objectClass=user) (|(mail=%u)(sAMAccountName=%u)) )", content)

        self.localconfig.refresh_from_db()
        self.assertFalse(self.localconfig.need_dovecot_update)
