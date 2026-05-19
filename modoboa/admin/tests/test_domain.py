"""Domain related test cases."""

import os
import shutil
import tempfile

from rest_framework import serializers as drf_serializers
from rq import SimpleWorker
from testfixtures import compare

from django.core.management import call_command
from django.urls import reverse

import django_rq

from modoboa.admin import signals as admin_signals
from modoboa.admin.api.v2 import serializers as admin_v2_serializers
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
        """Check that key length change triggers a new key creation."""
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
        queue = django_rq.get_queue("dkim")
        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)
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
        worker.work(burst=True)
        self.assertTrue(os.path.exists(key_path))


class DomainSerializerPluginSignalsTestCase(ModoAPITestCase):
    """Cover the four signals plugins use to extend ``DomainSerializer``."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        factories.populate_database()

    def setUp(self):
        super().setUp()
        self.create_calls = []
        self.update_calls = []

        sender = admin_v2_serializers.DomainSerializer

        def add_field(sender, **kwargs):
            return {
                "extra_field": drf_serializers.CharField(
                    required=False, allow_blank=True, allow_null=True, write_only=True
                )
            }

        def add_data(sender, domain, **kwargs):
            return {"extra_field": f"data-for-{domain.name}"}

        def on_create(sender, domain, plugin_data, request, **kwargs):
            self.create_calls.append((domain.name, dict(plugin_data)))

        def on_update(sender, domain, plugin_data, request, **kwargs):
            self.update_calls.append((domain.name, dict(plugin_data)))

        admin_signals.extra_domain_serializer_fields.connect(add_field, sender=sender)
        admin_signals.extra_domain_serializer_data.connect(add_data, sender=sender)
        admin_signals.domain_post_create_via_api.connect(on_create, sender=sender)
        admin_signals.domain_post_update_via_api.connect(on_update, sender=sender)

        self.addCleanup(
            admin_signals.extra_domain_serializer_fields.disconnect,
            add_field,
            sender=sender,
        )
        self.addCleanup(
            admin_signals.extra_domain_serializer_data.disconnect,
            add_data,
            sender=sender,
        )
        self.addCleanup(
            admin_signals.domain_post_create_via_api.disconnect,
            on_create,
            sender=sender,
        )
        self.addCleanup(
            admin_signals.domain_post_update_via_api.disconnect,
            on_update,
            sender=sender,
        )

    def test_extra_data_signal_appears_in_retrieve(self):
        """``extra_domain_serializer_data`` injects values into GET responses."""
        domain = Domain.objects.get(name="test.com")
        response = self.client.get(reverse("v2:domain-detail", args=[domain.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["extra_field"], "data-for-test.com")

    def test_extra_data_signal_appears_in_list(self):
        """The data signal also fires for the list endpoint."""
        response = self.client.get(reverse("v2:domain-list"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        results = body.get("results", body)
        for entry in results:
            self.assertEqual(entry["extra_field"], f"data-for-{entry['name']}")

    def test_create_signal_receives_plugin_data(self):
        """Plugin field is popped before super().create() and forwarded."""
        values = {
            "name": "ext-create.com",
            "quota": 0,
            "default_mailbox_quota": 0,
            "type": "domain",
            "extra_field": "hello",
        }
        response = self.client.post(reverse("v2:domain-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        # Domain was created; the plugin field never reaches the model.
        domain = Domain.objects.get(name="ext-create.com")
        self.assertFalse(hasattr(domain, "extra_field"))
        # ...but the receiver got it.
        self.assertEqual(
            self.create_calls, [("ext-create.com", {"extra_field": "hello"})]
        )

    def test_create_signal_fires_with_empty_plugin_data_when_field_omitted(self):
        """The receiver still fires when no plugin field is sent."""
        values = {
            "name": "ext-create-empty.com",
            "quota": 0,
            "default_mailbox_quota": 0,
            "type": "domain",
        }
        response = self.client.post(reverse("v2:domain-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.create_calls, [("ext-create-empty.com", {})])

    def test_update_signal_receives_plugin_data(self):
        """Plugin field is popped on update and forwarded to the post-update signal."""
        domain = Domain.objects.get(name="test.com")
        values = {
            "name": domain.name,
            "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota,
            "enabled": domain.enabled,
            "type": domain.type,
            "extra_field": "updated",
        }
        response = self.client.put(
            reverse("v2:domain-detail", args=[domain.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.update_calls, [("test.com", {"extra_field": "updated"})])
