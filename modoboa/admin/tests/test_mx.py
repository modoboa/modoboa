"""DNSBL related tests."""

from django.core import management
from django.core.urlresolvers import reverse
from django.test import override_settings

from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import models


class MXTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super(MXTestCase, cls).setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        factories.DomainFactory(name="pouet.com")  # should not exist

    def test_management_command(self):
        """Check that command works fine."""
        self.assertEqual(models.MXRecord.objects.count(), 0)
        management.call_command("modo", "check_mx", "--no-dnsbl",
                                "--valid-mx=127.0.0.1", "--ttl=0")
        self.assertTrue(
            models.MXRecord.objects.filter(domain=self.domain).exists())

        # we passed a ttl to 0. this will reset the cache this time
        qs = models.MXRecord.objects.filter(domain=self.domain)
        id = qs[0].id
        management.call_command("modo", "check_mx", "--no-dnsbl",
                                "--valid-mx=127.0.0.1", "--ttl=7200")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertNotEqual(id, qs[0].id)
        id = qs[0].id

        # assume that mxrecords ids are the same. means that we taking care of
        # ttl
        management.call_command("modo", "check_mx", "--no-dnsbl",
                                "--valid-mx=127.0.0.1")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertEqual(id, qs[0].id)


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
        management.call_command("modo", "check_mx")
        self.assertTrue(
            models.DNSBLResult.objects.filter(domain=self.domain).exists())
        response = self.client.get(
            reverse("admin:dnsbl_domain_detail", args=[self.domain.pk]))
        self.assertEqual(response.status_code, 200)

    @override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
    def test_management_command_no_dnsbl(self):
        """Check that command works fine without dnsbl."""
        self.assertEqual(models.DNSBLResult.objects.count(), 0)
        management.call_command("modo", "check_mx", "--no-dnsbl")
        self.assertFalse(
            models.DNSBLResult.objects.filter(domain=self.domain).exists())
        response = self.client.get(
            reverse("admin:dnsbl_domain_detail", args=[self.domain.pk]))
        self.assertEqual(response.status_code, 200)
