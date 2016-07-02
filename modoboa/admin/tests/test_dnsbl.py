"""DNSBL related tests."""

from django.core import management
from django.core.urlresolvers import reverse
from django.test import override_settings

from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import models


class DNSBLTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super(DNSBLTestCase, cls).setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        factories.DomainFactory(name="pouet.com")  # should not exist

    @override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
    def test_management_command(self):
        """Check that command works fine."""
        self.assertEqual(models.DNSBLResult.objects.count(), 0)
        management.call_command("modo", "check_dnsbl")
        self.assertTrue(
            models.DNSBLResult.objects.filter(domain=self.domain).exists())
        response = self.client.get(
            reverse("admin:dnsbl_domain_detail", args=[self.domain.pk]))
        self.assertEqual(response.status_code, 200)
