"""App related tests."""

from unittest import mock

from django.urls import reverse
from django.test import SimpleTestCase

from dns.rdtypes.ANY.TXT import TXT

from modoboa.lib.tests import ModoTestCase

from . import factories
from . import lib


BAD_SPF_RECORDS = [
    ("a mx ~all", "Not an SPF record"),
    ("v=spf1 toto ~all", "Unknown mechanism toto"),
    ("v=spf1 ip4 -all", "Wrong ip4 mechanism syntax"),
    ("v=spf1 +ip4:1.1.1. +all", "Wrong IPv4 address format"),
    ("v=spf1 ip6 ~all", "Wrong ip6 mechanism syntax"),
    ("v=spf1 +ip6:x:: +all", "Wrong IPv6 address format"),
    ("v=spf1 a|domain.com ~all", "Invalid syntax for a mechanism"),
    ("v=spf1 a:domain.com/TOTO", "Invalid mask found TOTO"),
    ("v=spf1 a/1000", "Invalid mask found 1000"),
    ("v=spf1 mx:domain.com/TOTO", "Invalid mask found TOTO"),
    ("v=spf1 mx/1000", "Invalid mask found 1000"),
    ("v=spf1 ptr|test.com", "Invalid syntax for ptr mechanism"),
    ("v=spf1 forward=test.com ~all", "Unknown modifier forward"),
    ("v=spf1 redirect=test.com redirect=test.com ~all",
     "Duplicate modifier redirect found"),
    ("v=spf1", "No mechanism found"),
]

GOOD_SPF_RECORDS = [
    "v=spf1 mx",
    "v=spf1 a ~all",
    "v=spf1 ip4:1.2.3.4 -all",
    "v=spf1 ip4:1.2.3.4/16 -all",
    "v=spf1 ip6:fe80::9eb6:d0ff:fe8e:2807 -all",
    "v=spf1 ip6:fe80::9eb6:d0ff:fe8e:2807/64 -all",
    "v=spf1 a -all",
    "v=spf1 a:example.com -all",
    "v=spf1 a:mailers.example.com -all",
    "v=spf1 a/24 a:offsite.example.com/24 -all",
    "v=spf1 mx mx:deferrals.domain.com -all",
    "v=spf1 mx/24 mx:offsite.domain.com/24 -all",
    "v=spf1 ptr -all",
    "v=spf1 ptr:otherdomain.com -all",
    "v=spf1 exists:example.com -all",
    "v=spf1 include:example.com  -all",
    "v=spf1 ?include:example.com -all",
    "v=spf1 redirect=example.com",
    "v=spf1 exp=example.com",
]

BAD_DMARC_RECORDS = [
    ("", "Not a valid DMARC record"),
    ("v=DMARC1; test", "Invalid tag test"),
    ("v=DMARC1; test=toto", "Unknown tag test"),
    ("v=DMARC1; adkim=g", "Wrong value g for tag adkim"),
    ("v=DMARC1; rua=mail:toto@test.com",
     "Wrong value mail:toto@test.com for tag rua"),
    ("v=DMARC1; rf=afrf,toto", "Wrong value toto for tag rf"),
    ("v=DMARC1; ri=XXX", "Wrong value XXX for tag ri: not an integer"),
    ("v=DMARC1; pct=-1", "Wrong value -1 for tag pct: less than 0"),
    ("v=DMARC1; pct=1000", "Wrong value 1000 for tag pct: greater than 100"),
    ("v=DMARC1; pct=100", "Missing required p tag"),
]

GOOD_DMARC_RECORDS = [
    "v=DMARC1; p=reject;; pct=100",
    "v=DMARC1; p=quarantine; sp=none; adkim=s; aspf=s; "
    "rua=mailto:dmarc-aggrep@ngyn.org; ruf=mailto:toto@test.com!24m; "
    "rf=afrf; pct=100; ri=86400"
]

BAD_DKIM_RECORDS = [
    ("", "Not a valid DKIM record"),
    ("v=DKIM1; toto;p=XXX", "Invalid tag toto"),
    ("v=DKIM1;;k=rsa", "No key found in record"),
]


class LibTestCase(SimpleTestCase):
    """TestCase for library methods."""

    @mock.patch('modoboa.admin.lib.get_dns_records')
    def test_get_record_type_value(self, mock_get_dns_records):
        mock_get_dns_records.return_value = [
            TXT("IN", "TXT", ["v=spf1 mx -all"]),
            TXT("IN", "TXT", ["v=DKIM1 p=XXXXX", "YYYYY"]),
            TXT("IN", "TXT", ["v=DMARC1 p=reject"]),
        ]
        self.assertEqual(
            lib.get_spf_record("example.com"), "v=spf1 mx -all"
        )
        self.assertEqual(
            lib.get_dkim_record("example.com", "mail"), "v=DKIM1 p=XXXXXYYYYY"
        )
        self.assertEqual(
            lib.get_dmarc_record("example.com"), "v=DMARC1 p=reject"
        )

    def test_check_spf_syntax(self):
        for record in BAD_SPF_RECORDS:
            with self.assertRaises(lib.DNSSyntaxError) as ctx:
                lib.check_spf_syntax(record[0])
            self.assertEqual(str(ctx.exception), record[1])
        for record in GOOD_SPF_RECORDS:
            lib.check_spf_syntax(record)

    def test_check_dmarc_syntax(self):
        for record in BAD_DMARC_RECORDS:
            with self.assertRaises(lib.DNSSyntaxError) as ctx:
                lib.check_dmarc_syntax(record[0])
            self.assertEqual(str(ctx.exception), record[1])
        for record in GOOD_DMARC_RECORDS:
            lib.check_dmarc_syntax(record)

    def test_check_dkim_syntax(self):
        for record in BAD_DKIM_RECORDS:
            with self.assertRaises(lib.DNSSyntaxError) as ctx:
                lib.check_dkim_syntax(record[0])
            self.assertEqual(str(ctx.exception), record[1])
        key = lib.check_dkim_syntax("v=DKIM1;p=XXX123")
        self.assertEqual(key, "XXX123")


class ViewsTestCase(ModoTestCase):
    """A test case for views."""

    @classmethod
    def setUpTestData(cls):
        """Create some records."""
        super(ViewsTestCase, cls).setUpTestData()
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

    def test_record_detail_view(self):
        url = reverse("dnstools:dns_record_detail", args=[self.spf_rec.pk])
        response = self.client.get(url)
        self.assertContains(
            response, "A DNS record has been found and is valid")
        url = reverse("dnstools:dns_record_detail", args=[self.dmarc_rec.pk])
        response = self.client.get(url)
        self.assertContains(response, "Not a DMARC record")

    def test_autoconfig_record_status_view(self):
        url = reverse(
            "dnstools:autoconfig_records_status", args=[self.ac_rec.domain.pk])
        response = self.client.get(url)
        self.assertContains(response, "autoconfig record (Mozilla) found")
        self.assertContains(
            response, "autodiscover record (Microsoft) not found")

    def test_domain_dns_configuration(self):
        url = reverse(
            "dnstools:domain_dns_configuration", args=[self.ac_rec.domain.pk])
        response = self.client.get(url)
        self.assertContains(response, "[IP address of your Modoboa server]")
