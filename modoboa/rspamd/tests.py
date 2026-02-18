import os
import shutil

from rq import SimpleWorker
from testfixtures import LogCapture

from django.test import modify_settings
from django.urls import reverse

import django_rq

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.rspamd import jobs


@modify_settings(
    INSTALLED_APPS={
        "append": "modoboa.rspamd",
    }
)
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

    def test_job(self):
        self.unconfigure()
        with LogCapture("modoboa.jobs") as log:
            jobs.update_rspamd_maps(
                list(admin_models.Domain.objects.all().values_list("id", flat=True))
            )
        log.check(
            (
                "modoboa.jobs",
                "ERROR",
                "path map path and/or selector map path "
                "not set in modoboa rspamd settings.",
            )
        )

        self.configure()
        jobs.update_rspamd_maps(
            list(admin_models.Domain.objects.all().values_list("id", flat=True))
        )
        self.assertFalse(os.path.exists(self.key_map_path))
        self.assertFalse(os.path.exists(self.selector_map_path))

        domain = admin_models.Domain.objects.get(name="test.com")
        domain.enable_dkim = True
        domain.dkim_private_key_path = "xxx"
        domain.save()
        jobs.update_rspamd_maps(
            list(admin_models.Domain.objects.all().values_list("id", flat=True))
        )
        self.assertTrue(os.path.exists(self.key_map_path))
        self.assertTrue(os.path.exists(self.selector_map_path))

        # Now, empty map files
        domain.enable_dkim = False
        domain.save()
        jobs.update_rspamd_maps(
            list(admin_models.Domain.objects.all().values_list("id", flat=True))
        )
        with open(self.key_map_path) as fp:
            content = fp.read()
        self.assertNotIn(domain.name, content)

    def test_signal_handler(self):
        self.set_global_parameter("dkim_keys_storage_dir", self.workdir, app="admin")
        self.configure()
        values = {
            "name": "pouet.com",
            "quota": 1000,
            "default_mailbox_quota": 100,
            "type": "domain",
            "enable_dkim": True,
        }
        url = reverse("v2:domain-list")
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)

        queue = django_rq.get_queue("dkim")
        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

        queue = django_rq.get_queue("modoboa")
        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

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


@modify_settings(
    MODOBOA_APPS={
        "append": "modoboa.rspamd",
    }
)
class CapabilitiesAPITestCase(ModoAPITestCase):

    def test_get(self):
        url = reverse("v2:capabilities")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("rspamd", response.json()["capabilities"])
