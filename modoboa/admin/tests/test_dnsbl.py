"""DNSBL related tests."""

from django.core import management
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
        factories.DomainFactory(name="modoboa.org")

    @override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
    def test_management_command(self):
        """Check that command works fine."""
        management.call_command("modo", "check_dnsbl")
        self.assertTrue(
            models.DNSBLResult.objects.filter(
                domain__name="modoboa.org").exists())
