# -*- coding: utf-8 -*-

"""DNSBL related tests."""

from __future__ import unicode_literals

import dns.resolver
from mock import patch
from testfixtures import LogCapture

from django.core import mail, management
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from modoboa.core import factories as core_factories
from modoboa.lib.tests import ModoTestCase
from . import utils
from .. import factories, models
from ..lib import get_domain_mx_list


class MXTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super(MXTestCase, cls).setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        # should not exist
        cls.bad_domain = factories.DomainFactory(
            name="does-not-exist.example.com")
        # Add domain admin with mailbox
        mb = factories.MailboxFactory(
            address="admin", domain=cls.bad_domain,
            user__username="admin@does-not-exist.example.com",
            user__groups=("DomainAdmins", )
        )
        cls.bad_domain.add_admin(mb.user)
        # Add domain admin with no mailbox
        admin = core_factories.UserFactory(
            username="admin2@does-not-exist.example.com",
            groups=("DomainAdmins", ))
        cls.bad_domain.add_admin(admin)

        cls.localconfig.parameters.set_value(
            "valid_mxs", "192.0.2.1 2001:db8::1")
        cls.localconfig.save()
        models.MXRecord.objects.all().delete()

    @patch("gevent.socket.gethostbyname")
    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_management_command(
            self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check that command works fine."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.assertEqual(models.MXRecord.objects.count(), 0)
        management.call_command("modo", "check_mx", "--no-dnsbl", "--ttl=0")
        self.assertTrue(
            models.MXRecord.objects.filter(domain=self.domain).exists())

        # we passed a ttl to 0. this will reset the cache this time
        qs = models.MXRecord.objects.filter(domain=self.domain)
        id_ = qs[0].id
        management.call_command("modo", "check_mx", "--no-dnsbl", "--ttl=7200")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertNotEqual(id_, qs[0].id)
        id_ = qs[0].id

        # assume that mxrecords ids are the same. means that we taking care of
        # ttl
        management.call_command("modo", "check_mx", "--no-dnsbl")
        qs = models.MXRecord.objects.filter(domain=self.domain)
        self.assertEqual(id_, qs[0].id)

    @patch("gevent.socket.gethostbyname")
    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_single_domain_update(
            self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Update only one domain."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
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
        self.assertEqual(len(mail.outbox), 1)

        management.call_command(
            "modo", "check_mx", "--domain", "toto.com")

    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_get_domain_mx_list_logging(self, mock_query, mock_getaddrinfo):
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        with LogCapture("modoboa.admin") as log:
            get_domain_mx_list("does-not-exist.example.com")
            get_domain_mx_list("no-mx.example.com")
            get_domain_mx_list("no-ns-servers.example.com")
            get_domain_mx_list("timeout.example.com")
            get_domain_mx_list("no-lookup.example.com")
            get_domain_mx_list("bad-response.example.com")
        log.check(
            ("modoboa.admin", "ERROR",
                _("No DNS records found for %s")
                % "does-not-exist.example.com"),
            ("modoboa.admin", "ERROR",
                _("No MX record for %s") % "no-mx.example.com"),
            ("modoboa.admin", "ERROR", _("No working name servers found")),
            ("modoboa.admin", "WARNING",
                _("DNS resolution timeout, unable to query %s at the moment")
                % "timeout.example.com"),
            ("modoboa.admin", "WARNING",
                _("Unable to lookup ip addresses for %(domain)s; %(error)s")
                % {"domain": "does-not-exist.example.com", "error": ""}),
            ("modoboa.admin", "WARNING",
                _("Invalid IP address format for %(domain)s; %(addr)s")
                % {"domain": "bad-response.example.com", "addr": "BAD"}),
        )


@override_settings(DNSBL_PROVIDERS=["zen.spamhaus.org"])
class DNSBLTestCase(ModoTestCase):
    """TestCase for DNSBL related features."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super(DNSBLTestCase, cls).setUpTestData()
        cls.domain = factories.DomainFactory(name="modoboa.org")
        factories.DomainFactory(name="does-not-exist.example.com")
        cls.domain2 = factories.DomainFactory(
            name="test.localhost")  # Should not be checked
        cls.domain3 = factories.DomainFactory(
            name="modoboa.com", enable_dns_checks=False)
        models.DNSBLResult.objects.all().delete()

    @patch("gevent.socket.gethostbyname")
    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_management_command(
            self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check that command works fine."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
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

    @patch("gevent.socket.gethostbyname")
    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_notifications(
            self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check notifications."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        management.call_command(
            "modo", "check_mx", "--email", "user@example.test")
        if len(mail.outbox) != 2:
            for message in mail.outbox:
                print(message.subject)
        self.assertEqual(len(mail.outbox), 2)

    @patch("gevent.socket.gethostbyname")
    @patch("socket.getaddrinfo")
    @patch.object(dns.resolver.Resolver, "query")
    def test_management_command_no_dnsbl(
            self, mock_query, mock_getaddrinfo, mock_g_gethostbyname):
        """Check that command works fine without dnsbl."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        mock_g_gethostbyname.return_value = "1.2.3.4"
        self.assertEqual(models.DNSBLResult.objects.count(), 0)
        management.call_command("modo", "check_mx", "--no-dnsbl")
        self.assertFalse(
            models.DNSBLResult.objects.filter(domain=self.domain).exists())
        response = self.client.get(
            reverse("admin:dnsbl_domain_detail", args=[self.domain.pk]))
        self.assertEqual(response.status_code, 200)
