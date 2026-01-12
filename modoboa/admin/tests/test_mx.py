"""DNSBL related tests."""

from unittest import mock

import dns.resolver
from rq import SimpleWorker
from testfixtures import LogCapture

from django.core import mail
from django.test import override_settings
from django.utils.translation import gettext as _

import django_rq

from modoboa.admin import jobs
from modoboa.admin.dns_checker import DNSChecker
from modoboa.core import models as core_models, factories as core_factories
from modoboa.lib.tests import ModoTestCase
from . import utils
from .. import factories, models
from ..lib import get_domain_mx_list


class MXTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        # should not exist
        cls.bad_domain = factories.DomainFactory(name="does-not-exist.example.com")
        # Add domain admin with mailbox
        mb = factories.MailboxFactory(
            address="admin",
            domain=cls.bad_domain,
            user__username="admin@does-not-exist.example.com",
            user__groups=("DomainAdmins",),
        )
        cls.bad_domain.add_admin(mb.user)
        # Add domain admin with no mailbox
        admin = core_factories.UserFactory(
            username="admin2@does-not-exist.example.com", groups=("DomainAdmins",)
        )
        cls.bad_domain.add_admin(admin)

        cls.localconfig.parameters.set_value("valid_mxs", "192.0.2.1 2001:db8::1")
        cls.localconfig.save()
        models.MXRecord.objects.all().delete()

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_dns_checker(self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check that command works fine."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.set_global_parameter("enable_dnsbl_checks", False)

        self.assertEqual(models.MXRecord.objects.count(), 0)
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain, ttl=0)
        self.assertTrue(models.MXRecord.objects.filter(domain=self.domain).exists())

        # we passed a ttl to 0. this will reset the cache this time
        qs = models.MXRecord.objects.filter(domain=self.domain)
        id_ = qs[0].id
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain)
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertNotEqual(id_, qs[0].id)
        id_ = qs[0].id

        # assume that mxrecords ids are the same. means that we taking care of
        # ttl
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain)
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertEqual(id_, qs[0].id)

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_invalid_mx(self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Test to check if invalid MX records are detected."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.set_global_parameter("enable_dnsbl_checks", False)

        domain = factories.DomainFactory(name="invalid-mx.com")
        # Add domain admin with mailbox
        mb = factories.MailboxFactory(
            address="admin",
            domain=domain,
            user__username=f"admin@{domain.name}",
            user__groups=("DomainAdmins",),
        )
        domain.add_admin(mb.user)
        with LogCapture("modoboa.dns"):
            DNSChecker().run(domain)
        self.assertEqual(domain.alarms.count(), 1)
        with LogCapture("modoboa.dns"):
            DNSChecker().run(domain)
        self.assertEqual(domain.alarms.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_get_mx_list_dns_server(self, mock_query, mock_getaddrinfo):
        """Test to get mx list from specific DNS server."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        self.set_global_parameter("custom_dns_server", "123.45.67.89")
        with LogCapture("modoboa.dns"):
            get_domain_mx_list("does-not-exist.example.com")

    @mock.patch("ipaddress.ip_address")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_get_domain_mx_list_logging(self, mock_query, mock_ip_address):
        """Test to get error loggins from specific DNS server."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_ip_address.side_effect = utils.mock_ip_address_result
        with LogCapture("modoboa.dns") as log:
            get_domain_mx_list("does-not-exist.example.com")
            get_domain_mx_list("no-mx.example.com")
            get_domain_mx_list("no-ns-servers.example.com")
            get_domain_mx_list("timeout.example.com")
            get_domain_mx_list("no-lookup.example.com")
            get_domain_mx_list("no-answer.example.Com")
            get_domain_mx_list("bad-response.example.com")
        log.check(
            (
                "modoboa.dns",
                "ERROR",
                _("No DNS record found for %s") % "does-not-exist.example.com",
            ),
            ("modoboa.dns", "ERROR", _("No MX record for %s") % "no-mx.example.com"),
            ("modoboa.dns", "ERROR", _("No working name servers found")),
            (
                "modoboa.dns",
                "WARNING",
                _("DNS resolution timeout, unable to query %s at the moment")
                % "timeout.example.com",
            ),
            (
                "modoboa.dns",
                "ERROR",
                _("No DNS record found for %s") % "does-not-exist.example.com",
            ),
            (
                "modoboa.dns",
                "ERROR",
                _("No DNS record found for %s") % "does-not-exist.example.com",
            ),
            (
                "modoboa.dns",
                "WARNING",
                _("Invalid IP address format for %(domain)s; %(addr)s")
                % {"domain": "bad-response.example.com", "addr": "000.0.0.0"},
            ),
            (
                "modoboa.dns",
                "WARNING",
                _("Invalid IP address format for %(domain)s; %(addr)s")
                % {"domain": "bad-response.example.com", "addr": "000.0.0.0"},
            ),
        )

    @mock.patch("ipaddress.ip_address")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_ipv6_logging(self, mock_query, mock_ip_address):
        """Test to check that AAAA missing record is logged consistently."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_ip_address.side_effect = utils.mock_ip_address_result
        localconfig = core_models.LocalConfig.objects.first()
        localconfig.parameters.set_value("enable_ipv6_mx_checks", True, "admin")
        localconfig.save()
        with LogCapture("modoboa.dns") as log:
            get_domain_mx_list("test3.com")
        log.check(
            ("modoboa.dns", "ERROR", _("No AAAA record for %s") % "mx3.example.com")
        )
        localconfig = core_models.LocalConfig.objects.first()
        localconfig.parameters.set_value("enable_ipv6_mx_checks", False, "admin")
        localconfig.save()
        with LogCapture("modoboa.dns") as log2:
            get_domain_mx_list("test3.com")
        log2.check()


@override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
class DNSBLTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        # Add domain admin with mailbox
        mb = factories.MailboxFactory(
            address="admin",
            domain=cls.domain,
            user__username="admin@modoboa.org",
            user__groups=("DomainAdmins",),
        )
        cls.domain.add_admin(mb.user)

        factories.DomainFactory(name="does-not-exist.example.com")
        cls.domain2 = factories.DomainFactory(
            name="test.localhost"
        )  # Should not be checked
        cls.domain3 = factories.DomainFactory(
            name="modoboa.com", enable_dns_checks=False
        )
        models.DNSBLResult.objects.all().delete()

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_job(self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check that command works fine."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.assertEqual(models.DNSBLResult.objects.count(), 0)

        queue = django_rq.get_queue("modoboa")
        worker = SimpleWorker([queue], connection=queue.connection)
        with LogCapture("modoboa.dns"):
            jobs.handle_dns_checks()
            worker.work(burst=True)
        self.assertTrue(models.DNSBLResult.objects.filter(domain=self.domain).exists())
        self.assertFalse(
            models.DNSBLResult.objects.filter(domain=self.domain3).exists()
        )
        self.assertFalse(self.domain.uses_a_reserved_tld)
        self.assertTrue(self.domain2.uses_a_reserved_tld)

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_notifications(self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check notifications."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "127.0.0.4"
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain)
        self.assertEqual(len(mail.outbox), 1)

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_notifications_wrong_dnsbl_response(
        self, mock_query, mock_getaddrinfo, mock_g_gethostbyname
    ):
        """Check notifications."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "127.255.255.254"  # <--Spamhaus response when querying from an open resolver
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain)
        self.assertEqual(len(mail.outbox), 1)

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_management_command_no_dnsbl(
        self, mock_query, mock_getaddrinfo, mock_g_gethostbyname
    ):
        """Check that command works fine without dnsbl."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.set_global_parameter("enable_dnsbl_checks", False)
        self.assertEqual(models.DNSBLResult.objects.count(), 0)
        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain)
        self.assertFalse(models.DNSBLResult.objects.filter(domain=self.domain).exists())


class DNSChecksTestCase(ModoTestCase):
    """A test case for DNS checks."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        cls.domain = factories.DomainFactory(name="dns-checks.com")

    @mock.patch("socket.gethostbyname")
    @mock.patch("socket.getaddrinfo")
    @mock.patch.object(dns.resolver.Resolver, "resolve")
    def test_management_command(
        self, mock_query, mock_getaddrinfo, mock_g_gethostbyname
    ):
        """Check that command works fine."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.set_global_parameter("enable_dnsbl_checks", False)

        self.domain.enable_dkim = True
        self.domain.dkim_public_key = "XXXXX"
        self.domain.save(update_fields=["enable_dkim", "dkim_public_key"])

        with LogCapture("modoboa.dns"):
            DNSChecker().run(self.domain, ttl=0)

        self.assertIsNot(self.domain.spf_record, None)
        self.assertIsNot(self.domain.dkim_record, None)
        self.assertIsNot(self.domain.dmarc_record, None)
        self.assertIsNot(self.domain.autoconfig_record, None)
        self.assertIsNot(self.domain.autodiscover_record, None)
