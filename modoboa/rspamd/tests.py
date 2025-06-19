import os
import shutil

from django.core import management
from django.urls import reverse

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

    def configure(self):
        self.key_map_path = f"{self.workdir}/keys.map"
        self.set_global_parameter("key_map_path", self.key_map_path)
        self.selector_map_path = f"{self.workdir}/selectors.map"
        self.set_global_parameter("selector_map_path", self.selector_map_path)

    def unconfigure(self):
        self.set_global_parameter("key_map_path", "")
        self.set_global_parameter("selector_map_path", "")

    def test_command(self):
        self.unconfigure()
        with self.assertRaises(management.CommandError):
            management.call_command("manage_rspamd_maps")

        self.configure()
        management.call_command("manage_rspamd_maps")
        self.assertFalse(os.path.exists(self.key_map_path))
        self.assertFalse(os.path.exists(self.selector_map_path))

        domain = admin_models.Domain.objects.get(name="test.com")
        domain.enable_dkim = True
        domain.dkim_private_key_path = "xxx"
        domain.save()
        management.call_command("manage_rspamd_maps")
        self.assertTrue(os.path.exists(self.key_map_path))
        self.assertTrue(os.path.exists(self.selector_map_path))

        # Now, empty map files
        domain.enable_dkim = False
        domain.save()
        management.call_command("manage_rspamd_maps")
        with open(self.key_map_path) as fp:
            content = fp.read()
        self.assertNotIn(domain.name, content)

    def test_command_with_arg(self):
        self.configure()
        domain = admin_models.Domain.objects.get(name="test.com")
        domain.enable_dkim = True
        domain.save()
        management.call_command("manage_rspamd_maps", "--domain", "test.com")
        self.assertTrue(os.path.exists(self.key_map_path))
        self.assertTrue(os.path.exists(self.selector_map_path))


class ParametersAPITestCase(ModoAPITestCase):

    def test_update_settings(self):
        url = reverse("v2:parameter-global-detail", args=["rspamd"])
        data = {
            "key_map_path": f"{self.workdir}/key.map",
            "selector_map_path": f"{self.workdir}/selector.map",
            "rspamd_dashboard_location": "/rspamd",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
