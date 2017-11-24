"""Transport tests."""

from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase

from . import factories
from . import models


class TransportTestCase(ModoTestCase):
    """Test transport views."""

    @classmethod
    def setUpTestData(cls):
        super(TransportTestCase, cls).setUpTestData()
        cls.transport1 = factories.TransportFactory(
            pattern="domain1.test", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": "25",
                "relay_verify_recipients": False
            }
        )
        cls.transport2 = factories.TransportFactory(
            pattern="domain2.test", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": "25",
                "relay_verify_recipients": True
            }
        )

    def test_transport_list(self):
        """Test list view."""
        url = reverse("transport:transport_list")
        response = self.client.get(url)
        self.assertContains(response, self.transport1.pattern)
        self.assertContains(response, self.transport2.pattern)

        url = "{}?searchquery=domain1".format(url)
        response = self.client.get(url)
        self.assertContains(response, self.transport1.pattern)
        self.assertNotContains(response, self.transport2.pattern)

    def test_create_transport(self):
        """Test create view."""
        url = reverse("transport:transport_create")
        response = self.client.get(url)
        self.assertContains(response, "New transport")
        data = {
            "pattern": "domain3.test",
            "service": "relay",
            "relay_target_host": "1.2.3.4",
        }
        response = self.ajax_post(url, data, 400)

        data.update({"relay_target_port": 25})
        self.ajax_post(url, data)
        transport = models.Transport.objects.get(pattern="domain3.test")
        self.assertEqual(
            transport.next_hop, "[{}]:{}".format(
                data["relay_target_host"], data["relay_target_port"])
        )

    def test_update_transport(self):
        """Test update view."""
        url = reverse("transport:transport_update", args=[self.transport1.pk])
        response = self.client.get(url)
        self.assertContains(response, "Edit transport")
        data = {
            "pattern": self.transport1.pattern,
            "service": self.transport1.service,
            "relay_target_host": "1.2.3.5",
            "relay_target_port": 234,
            "relay_verify_recipients": True
        }
        self.ajax_post(url, data)
        self.transport1.refresh_from_db()
        self.assertTrue(
            self.transport1._settings["relay_verify_recipients"])
        self.assertEqual(
            self.transport1.next_hop, "[{}]:{}".format(
                data["relay_target_host"], data["relay_target_port"])
        )

    def test_delete_transport(self):
        """Test delete view."""
        url = reverse("transport:transport_delete", args=[self.transport1.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(models.Transport.DoesNotExist):
            self.transport1.refresh_from_db()
