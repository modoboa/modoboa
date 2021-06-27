"""API v2 tests."""

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.dnstools import factories
from modoboa.lib.tests import ModoAPITestCase


class DNSViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.spf_rec = factories.DNSRecordFactory(
            type="spf", value="v=SPF1 mx -all", is_valid=True,
            domain__name="test.com"
        )
        cls.dmarc_rec = factories.DNSRecordFactory(
            type="dmarc", value="XXX", is_valid=False,
            error="Not a DMARC record",
            domain__name="test.com"
        )
        cls.dkim_rec = factories.DNSRecordFactory(
            type="dkim", value="12345", is_valid=False,
            error="Public key mismatchs",
            domain__name="test.com"
        )
        cls.ac_rec = factories.DNSRecordFactory(
            type="autoconfig", value="1.2.3.4", is_valid=True,
            domain__name="test.com"
        )

    def test_dns_detail(self):
        domain = admin_models.Domain.objects.get(name="test.com")
        url = reverse("v2:dns-dns-detail", args=[domain.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["dmarc_record"]["type"], "dmarc")
