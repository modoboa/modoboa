"""Domain related test cases."""

import os
import shutil
import tempfile

from testfixtures import compare

from django.core.management import call_command
from django.urls import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase, SETTINGS_SAMPLE

from .. import constants
from .. import factories
from ..models import Alarm, Alias, Domain


class DomainTestCase(ModoAPITestCase):
    """Test case for Domain."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_create_with_template_and_empty_quota(self):
        """Test the creation of a domain with a template and no quota"""
        values = {
            "name": "pouet.com",
            "quota": 0,
            "default_mailbox_quota": 0,
            "domain_admin": {
                "username": "toto",
                "with_mailbox": True,
                "with_aliases": True,
            },
            "type": "domain",
        }
        response = self.client.post(reverse("v2:domain-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(al.aliasrecipient_set.filter(r_mailbox=da.mailbox).exists())
        self.assertTrue(da.can_access(al))

    def test_quota_constraints(self):
        """Check quota constraints."""
        values = {
            "name": "pouet.com",
            "quota": 10,
            "default_mailbox_quota": 100,
            "domain_admin": {
                "username": "toto",
                "with_mailbox": True,
                "with_aliases": True,
            },
            "type": "domain",
        }
        response = self.client.post(reverse("v2:domain-list"), values, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["default_mailbox_quota"][0],
            "Cannot be greater than domain quota",
        )

        dom = Domain.objects.get(name="test.com")
        values["name"] = dom.name
        values["quota"] = 10
        values["default_mailbox_quota"] = 100
        response = self.client.put(
            reverse("v2:domain-detail", args=[dom.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["default_mailbox_quota"][0],
            "Cannot be greater than domain quota",
        )

    def test_domain_counters(self):
        """Check counters at domain level."""
        domain = Domain.objects.get(name="test.com")
        self.assertEqual(domain.domainalias_count, 0)
        self.assertEqual(domain.mailbox_count, 2)
        self.assertEqual(domain.mbalias_count, 3)
        self.assertEqual(domain.identities_count, 5)


class DKIMTestCase(ModoAPITestCase):
    """Test case for DKIM."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def setUp(self):
        super().setUp()
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_global_settings(self):
        """Check validation rules."""
        url = reverse("v2:parameter-global-detail", args=["admin"])
        settings = SETTINGS_SAMPLE["admin"].copy()
        settings["dkim_keys_storage_dir"] = "/wrong"
        response = self.client.put(url, settings, format="json")
        self.assertEqual(response.status_code, 400)
        compare(response.json(), {"dkim_keys_storage_dir": ["Directory not found."]})
        settings["dkim_keys_storage_dir"] = self.workdir
        response = self.client.put(url, settings, format="json")
        self.assertEqual(response.status_code, 200)

    def test_dkim_key_creation(self):
        """Test DKIM key creation."""
        values = {
            "name": "pouet.com",
            "quota": 1000,
            "default_mailbox_quota": 100,
            "type": "domain",
            "enable_dkim": True,
        }
        url = reverse("v2:domain-list")
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["enable_dkim"][0],
            "DKIM keys storage directory not configured",
        )

        self.set_global_parameter("dkim_keys_storage_dir", self.workdir)
        values["dkim_key_selector"] = "default"
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)

        # Try generating a key to a protected directory
        self.set_global_parameter("dkim_keys_storage_dir", "/I_DONT_EXIST")
        call_command("modo", "manage_dkim_keys")
        domain = Domain.objects.get(name=values["name"])

        # Closing the alarm and retry generating dkim keys
        Alarm.objects.get(
            domain=domain, internal_name=constants.DKIM_WRITE_ERROR
        ).close()
        call_command("modo", "manage_dkim_keys")
        self.assertEqual(
            Alarm.objects.get(
                domain=domain, internal_name=constants.DKIM_WRITE_ERROR
            ).status,
            constants.ALARM_OPENED,
        )

        # Generate normally
        self.set_global_parameter("dkim_keys_storage_dir", self.workdir)
        call_command("modo", "manage_dkim_keys")
        self.assertEqual(
            Alarm.objects.get(
                domain=domain, internal_name=constants.DKIM_WRITE_ERROR
            ).status,
            constants.ALARM_CLOSED,
        )
        key_path = os.path.join(self.workdir, "{}.pem".format(values["name"]))
        self.assertTrue(os.path.exists(key_path))

        domain.refresh_from_db()

        # Try generating DKIM key for a targetted domain
        domain.dkim_private_key_path = ""
        domain.save()

        call_command("modo", "manage_dkim_keys", f"--domain={domain.name}")
        domain.refresh_from_db()
        self.assertNotEqual(domain.dkim_private_key_path, "")

        # Try disabling DKIM and checking that dkim_private_key_path is emptied
        values = {
            "name": "pouet.com",
            "enable_dkim": False,
            "quota": 1000,
            "default_mailbox_quota": 100,
            "type": "domain",
        }
        response = self.client.put(
            reverse("v2:domain-detail", args=[domain.id]), values, format="json"
        )
        domain.refresh_from_db()
        self.assertEqual(domain.dkim_private_key_path, "")

    def test_dkim_key_length_modification(self):
        """ """
        self.set_global_parameter("dkim_keys_storage_dir", self.workdir)
        values = {
            "name": "pouet.com",
            "quota": 1000,
            "default_mailbox_quota": 100,
            "type": "domain",
            "enable_dkim": True,
            "dkim_key_selector": "default",
        }
        url = reverse("v2:domain-list")
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)
        call_command("modo", "manage_dkim_keys")
        key_path = os.path.join(self.workdir, "{}.pem".format(values["name"]))
        self.assertTrue(os.path.exists(key_path))
        dom = Domain.objects.get(name="pouet.com")
        values["dkim_key_length"] = 4096
        response = self.client.put(
            reverse("v2:domain-detail", args=[dom.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        dom.refresh_from_db()
        self.assertEqual(dom.dkim_private_key_path, "")
        os.unlink(key_path)
        call_command("modo", "manage_dkim_keys")
        self.assertTrue(os.path.exists(key_path))
