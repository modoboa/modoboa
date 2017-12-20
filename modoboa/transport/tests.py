"""Transport tests."""

import json

from django.urls import reverse

from modoboa.lib.tests import ModoAPITestCase

from . import factories
from . import models


class DataMixin(object):
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):
        super(DataMixin, cls).setUpTestData()
        cls.transport1 = factories.TransportFactory(
            pattern="domain1.test", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": False
            }
        )
        cls.transport2 = factories.TransportFactory(
            pattern="domain2.test", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": True
            }
        )


class TransportAPITestCase(DataMixin, ModoAPITestCase):
    """API test cases."""

    def test_list(self):
        """Test list service."""
        url = reverse("api:transport-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_create(self):
        """Test create service."""
        url = reverse("api:transport-list")
        settings = {
            "relay_target_host": "1.2.3.4"
        }
        data = {
            "pattern": "domain3.test",
            "service": "relay",
            "_settings": json.dumps(settings)
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["_settings"],
            ["relay_target_port: This field is required"]
        )

        settings.update({"relay_target_port": 25})
        data["_settings"] = json.dumps(settings)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        transport = models.Transport.objects.get(pattern="domain3.test")
        self.assertEqual(
            transport.next_hop, "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"])
        )

    def test_update(self):
        """Test update service."""
        url = reverse("api:transport-detail", args=[self.transport1.pk])
        settings = self.transport1._settings.copy()
        settings.update({"relay_target_port": 1000})
        data = {
            "pattern": "domain3.test",
            "service": "relay",
            "_settings": json.dumps(settings)
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.transport1.refresh_from_db()
        self.assertEqual(self.transport1.pattern, data["pattern"])
        self.assertEqual(
            self.transport1.next_hop, "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"])
        )

    def test_delete(self):
        """Test delete service."""
        url = reverse("api:transport-detail", args=[self.transport1.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(models.Transport.DoesNotExist):
            self.transport1.refresh_from_db()
