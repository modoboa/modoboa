import os
import shutil

from django.core import management

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.lib.tests import ModoAPITestCase


class ManagementCommandTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def setUp(self):
        super().setUp()
        self.key_map_path = f"{self.workdir}/keys.map"
        self.set_global_parameter("key_map_path", self.key_map_path)
        self.selector_map_path = f"{self.workdir}/selectors.map"
        self.set_global_parameter("selector_map_path", self.selector_map_path)

    def test_command(self):
        management.call_command("manage_rspamd_maps")
        self.assertFalse(os.path.exists(self.key_map_path))
        self.assertFalse(os.path.exists(self.selector_map_path))

        domain = admin_models.Domain.objects.get(name="test.com")
        domain.enable_dkim = True
        domain.save()
        management.call_command("manage_rspamd_maps")
        self.assertTrue(os.path.exists(self.key_map_path))
        self.assertTrue(os.path.exists(self.selector_map_path))

    def test_command_with_arg(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.enable_dkim = True
        domain.save()
        management.call_command("manage_rspamd_maps", "--domain", "test.com")
        self.assertTrue(os.path.exists(self.key_map_path))
        self.assertTrue(os.path.exists(self.selector_map_path))
