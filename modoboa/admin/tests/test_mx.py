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
        # should not exist
        cls.bad_domain = factories.DomainFactory(name="pouet.com")
        cls.localconfig.parameters.set_value("valid_mxs", "127.0.0.1")
        cls.localconfig.save()
        models.MXRecord.objects.all().delete()

    def test_management_command(self):
        """Check that command works fine."""
        self.assertEqual(models.MXRecord.objects.count(), 0)
        management.call_command("modo", "check_mx", "--no-dnsbl", "--ttl=0")
        self.assertTrue(
            models.MXRecord.objects.filter(domain=self.domain).exists())

        # we passed a ttl to 0. this will reset the cache this time
        qs = models.MXRecord.objects.filter(domain=self.domain)
        id = qs[0].id
        management.call_command("modo", "check_mx", "--no-dnsbl", "--ttl=7200")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertNotEqual(id, qs[0].id)
        id = qs[0].id

        # assume that mxrecords ids are the same. means that we taking care of
        # ttl
        management.call_command("modo", "check_mx", "--no-dnsbl")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertEqual(id, qs[0].id)

    def test_single_domain_update(self):
        """Update only one domain."""
        management.call_command(
            "modo", "check_mx", "--domain", self.domain.name)
        self.assertTrue(
            models.MXRecord.objects.filter(domain=self.domain).exists())
        self.assertFalse(
            models.MXRecord.objects.filter(domain=self.bad_domain).exists())

        management.call_command(
            "modo", "check_mx", "--domain", str(self.bad_domain.pk))
        self.assertFalse(
            models.MXRecord.objects.filter(domain=self.bad_domain).exists())

        management.call_command(
            "modo", "check_mx", "--domain", "toto.com")


class DNSBLTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super(DNSBLTestCase, cls).setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        factories.DomainFactory(name="pouet.com")  # should not exist
        cls.domain2 = factories.DomainFactory(
            name="test.localhost")  # Should not be checked
        cls.domain3 = factories.DomainFactory(
            name="modoboa.com", enable_dns_checks=False)
        models.DNSBLResult.objects.all().delete()

    @override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
    def test_management_command(self):
        """Check that command works fine."""
        self.assertEqual(models.DNSBLResult.objects.count(), 0)
        management.call_command("modo", "check_mx")
        self.assertTrue(
            models.DNSBLResult.objects.filter(domain=self.domain).exists())
        self.assertFalse(
            models.DNSBLResult.objects.filter(domain=self.domain3).exists())
        response = self.client.get(
            reverse("admin:dnsbl_domain_detail", args=[self.domain.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.domain.uses_a_reserved_tld)
        self.assertTrue(self.domain2.uses_a_reserved_tld)

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
