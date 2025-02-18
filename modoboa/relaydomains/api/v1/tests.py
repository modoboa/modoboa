"""relaydomains API v1 unit tests."""

import json

from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.transport import factories as tr_factories, models as tr_models


class DataMixin:
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super().setUpTestData()
        transport = tr_factories.TransportFactory(
            pattern="test.com",
            _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": False,
            },
        )
        cls.domain1 = admin_factories.DomainFactory(
            name="test.com", type="relaydomain", transport=transport
        )
        transport = tr_factories.TransportFactory(
            pattern="domain2.test",
            _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": True,
            },
        )
        cls.domain2 = admin_factories.DomainFactory(
            name="test2.com", type="relaydomain", transport=transport
        )


class RelayDomainAPITestCase(DataMixin, ModoAPITestCase):
    """API test cases."""

    def test_list(self):
        """Test list service."""
        url = reverse("api:relaydomain-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_create(self):
        """Test create service."""
        url = reverse("api:relaydomain-list")
        settings = {"relay_target_host": "1.2.3.4"}
        data = {
            "name": "test3.com",
            "transport": {"service": "relay", "_settings": json.dumps(settings)},
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["transport"]["_settings"],
            ["relay_target_port: This field is required"],
        )

        settings.update({"relay_target_port": 25})
        data["transport"]["_settings"] = json.dumps(settings)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        domain = admin_models.Domain.objects.get(name="test3.com")
        self.assertEqual(
            domain.transport.next_hop,
            "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"]
            ),
        )

    def test_update(self):
        """Test update service."""
        url = reverse("api:relaydomain-detail", args=[self.domain1.pk])
        settings = self.domain1.transport._settings.copy()
        settings.update({"relay_target_port": 1000})
        data = {
            "name": "test3.com",
            "transport": {"service": "relay", "_settings": json.dumps(settings)},
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.domain1.refresh_from_db()
        self.domain1.transport.refresh_from_db()
        self.assertEqual(self.domain1.name, data["name"])
        self.assertEqual(
            self.domain1.transport.next_hop,
            "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"]
            ),
        )

    def test_delete(self):
        """Test delete service."""
        url = reverse("api:relaydomain-detail", args=[self.domain1.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(admin_models.Domain.DoesNotExist):
            self.domain1.refresh_from_db()
        self.assertFalse(
            tr_models.Transport.objects.filter(pattern="test.com").exists()
        )
