"""API v2 tests."""

from django.urls import reverse

from modoboa.lib.tests import ModoAPITestCase

from modoboa.admin import factories as admin_factories
from modoboa.dmarc.tests import mixins


class DmarcViewSetTestCase(mixins.CallCommandMixin, ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        cls.domain = admin_factories.DomainFactory(name="ngyn.org")

    def test_alignment_stats(self):
        """Test alignment stats endpoint."""
        self.import_reports()
        url = reverse("v2:dmarc-alignment-stats", args=[self.domain.pk])
        response = self.client.get(f"{url}?period=2015-26")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["failed"]), 1)

    def test_no_record(self):
        url = reverse("v2:dmarc-alignment-stats", args=[self.domain.pk])
        response = self.client.get(f"{url}?period=2015-26")
        self.assertEqual(response.status_code, 204)

    def test_wrong_range(self):
        self.import_reports()
        url = reverse("v2:dmarc-alignment-stats", args=[self.domain.pk])
        response = self.client.get(f"{url}?period=toto-titi")
        self.assertEqual(response.status_code, 400)
