"""Management command tests."""

import os
import shutil
import tempfile
from unittest import mock

from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from modoboa.core.tests.test_views import SETTINGS_SAMPLE

from modoboa.lib.tests import ModoTestCase
from .. import factories, models

class NeedDovecotUpdateTestCase(ModoTestCase):
    """Test need dovecot ldap update command."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(NeedDovecotUpdateTestCase, cls).setUpTestData()
        factories.populate_database()

    def setUp(self):
        """Initiate initial env."""
        super(NeedDovecotUpdateTestCase, self).setUp()
        self.workdir = tempfile.mkdtemp()
        path = "{}/test.com/admin".format(self.workdir)
        os.makedirs(path)

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def test_need_dovecot_update_singleton(self):
        need_dovecot_update = models.NeedDovecotUpdate.load()
        self.assertIsNotNone(need_dovecot_update)
        self.assertEqual(need_dovecot_update.pk, 1)
        #Reload test
        need_dovecot_update = models.NeedDovecotUpdate.load()
        self.assertEqual(need_dovecot_update.pk, 1)
        self.assertFalse(need_dovecot_update.state)
        self.assertEqual(models.NeedDovecotUpdate.objects.count(), 1)

    def test_need_dovecot_update_no_singleton_delete(self):
        need_dovecot_update = models.NeedDovecotUpdate.load()
        self.assertIsNotNone(need_dovecot_update)
        need_dovecot_update.delete()
        need_dovecot_update.refresh_from_db()
        self.assertIsNotNone(need_dovecot_update)

    def test_update_dovecot_update_state_valid_form(self):
        need_dovecot_update = models.NeedDovecotUpdate.load()
        self.assertFalse(need_dovecot_update.state)
        url = reverse("core:parameters")
        settings = SETTINGS_SAMPLE.copy()
        response = self.client.post(url, settings, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Parameters saved")
        self.assertEqual(models.NeedDovecotUpdate.objects.count(), 1)
        need_dovecot_update.refresh_from_db()
        self.assertTrue(need_dovecot_update.state)

    def test_update_dovecot_ldap_conf(self):
        need_dovecot_update = models.NeedDovecotUpdate.load()
        need_dovecot_update.state = True
        need_dovecot_update.save()
        self.assertTrue(need_dovecot_update.state)
        
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
        with open(tmp_file) as tmp:
            content = tmp.read()
        self.assertIn("uris = ldaps://localhost:636 ldaps://localhost2:636", content)
        self.assertIn("dn = \"DC=test,DC=lan\"", content)
        self.assertIn("dnpass = \'test\'", content)
        self.assertIn("base = CN=Users,DC=test,DC=lan", content)
        self.assertIn("user_filter = (& (objectClass=user) (|(mail=%u)(sAMAccountName=%u)) )", content)
        self.assertIn("pass_filter = (& (objectClass=user) (|(mail=%u)(sAMAccountName=%u)) )", content)
        
        need_dovecot_update.refresh_from_db()
        self.assertFalse(need_dovecot_update.state)
