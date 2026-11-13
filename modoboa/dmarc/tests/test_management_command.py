"""Management command tests."""

import io
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest import mock

from django.core.management import call_command

from modoboa.admin import factories as admin_factories
from modoboa.lib.tests import ModoTestCase

from . import mixins
from .. import models


class ManagementCommandTestCase(mixins.CallCommandMixin, ModoTestCase):
    """Test management command."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.domain = admin_factories.DomainFactory(name="ngyn.org")

    def test_import_from_archive(self):
        """Import report from archive."""
        self.import_reports()
        self.import_fail_reports()
        self.assertTrue(self.domain.record_set.exists())
        self.assertTrue(
            models.Reporter.objects.filter(org_name="FastMail Pty Ltd").exists()
        )
        # Ensure that reports from Yahoo are processed successfully.
        # These do not contain a sp attribute in policy_published
        self.assertTrue(
            models.Report.objects.filter(
                report_id="1435111091.916236",
                reporter=models.Reporter.objects.get(org_name="Yahoo! Inc."),
            ).exists()
        )

    def test_import_report_with_missing_auth_results_domain(self):
        """Import a report where auth_results have empty or missing domain/result.

        Regression test for #3846: the import would crash with an
        AttributeError when <domain> or <result> elements were missing
        or empty inside <auth_results>.
        """
        from ..lib import import_report

        xml = b"""<?xml version="1.0" encoding="UTF-8" ?>
<feedback>
  <report_metadata>
    <org_name>testprovider.com</org_name>
    <email>noreply-dmarc@testprovider.com</email>
    <report_id>missing-auth-domain-123</report_id>
    <date_range>
      <begin>1622592000</begin>
      <end>1622678399</end>
    </date_range>
  </report_metadata>
  <policy_published>
    <domain>ngyn.org</domain>
    <adkim>r</adkim>
    <aspf>r</aspf>
    <p>none</p>
    <sp>none</sp>
    <pct>100</pct>
  </policy_published>
  <record>
    <row>
      <source_ip>203.0.113.50</source_ip>
      <count>1</count>
      <policy_evaluated>
        <disposition>none</disposition>
        <dkim>pass</dkim>
        <spf>pass</spf>
      </policy_evaluated>
    </row>
    <identifiers>
      <header_from>ngyn.org</header_from>
    </identifiers>
    <auth_results>
      <dkim>
        <domain></domain>
        <result>pass</result>
      </dkim>
      <spf>
        <domain>ngyn.org</domain>
        <result></result>
      </spf>
    </auth_results>
  </record>
  <record>
    <row>
      <source_ip>203.0.113.51</source_ip>
      <count>2</count>
      <policy_evaluated>
        <disposition>none</disposition>
        <dkim>fail</dkim>
        <spf>pass</spf>
      </policy_evaluated>
    </row>
    <identifiers>
      <header_from>ngyn.org</header_from>
    </identifiers>
    <auth_results>
      <dkim>
        <result>fail</result>
      </dkim>
      <spf>
        <result>pass</result>
      </spf>
    </auth_results>
  </record>
</feedback>"""

        import_report(xml)

        report = models.Report.objects.get(report_id="missing-auth-domain-123")
        records = models.Record.objects.filter(report=report).order_by("source_ip")
        self.assertEqual(records.count(), 2)

        # First record: empty <domain> in dkim, empty <result> in spf
        rec1 = records[0]
        self.assertEqual(rec1.source_ip, "203.0.113.50")
        results1 = models.Result.objects.filter(record=rec1)
        dkim_result = results1.get(type="dkim")
        self.assertEqual(dkim_result.domain, "ngyn.org")
        self.assertEqual(dkim_result.result, "pass")
        spf_result = results1.get(type="spf")
        self.assertEqual(spf_result.domain, "ngyn.org")
        self.assertEqual(spf_result.result, "")

        # Second record: missing <domain> element entirely in both
        rec2 = records[1]
        self.assertEqual(rec2.source_ip, "203.0.113.51")
        results2 = models.Result.objects.filter(record=rec2)
        dkim_result2 = results2.get(type="dkim")
        self.assertEqual(dkim_result2.domain, "ngyn.org")
        self.assertEqual(dkim_result2.result, "fail")
        spf_result2 = results2.get(type="spf")
        self.assertEqual(spf_result2.domain, "ngyn.org")
        self.assertEqual(spf_result2.result, "pass")


def _report_email(xml: bytes) -> bytes:
    msg = MIMEMultipart()
    msg.attach(MIMEText(xml.decode(), "xml"))
    return msg.as_bytes()


MALFORMED_REPORTS = [
    # Truncated XML -> ParseError (a SyntaxError, not a ValueError)
    b'<?xml version="1.0" encoding="UTF-8" ?>\n<feedback><report_metadata>',
    # Well-formed but no <report_metadata> -> AttributeError
    b'<?xml version="1.0" encoding="UTF-8" ?>\n<feedback><record/></feedback>',
]


class MalformedReportTestCase(mixins.CallCommandMixin, ModoTestCase):
    """Malformed reports must be skipped, not crash the importer."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.domain = admin_factories.DomainFactory(name="ngyn.org")

    def test_pipe_malformed_report_exits_with_dataerr(self):
        for xml in MALFORMED_REPORTS:
            with self.subTest(xml=xml):
                sys.stdin = io.StringIO(_report_email(xml).decode())
                with self.assertRaisesMessage(SystemExit, "65"):
                    call_command(
                        "import_aggregated_report", "--pipe", stdout=io.StringIO()
                    )

    @mock.patch("modoboa.dmarc.lib.getpass.getpass", return_value="password")
    @mock.patch("builtins.input", return_value="user")
    @mock.patch("modoboa.dmarc.lib.imaplib.IMAP4")
    def test_imap_malformed_report_does_not_block_batch(self, imap_mock, *args):
        path = os.path.join(
            os.path.dirname(__file__),
            "reports",
            "Report_Domain_ngyn.org_Submitter_fastmail.com_Report-ID_2015.06.23.5672770.eml",
        )
        with open(path, "rb") as fp:
            good = fp.read()
        messages = [_report_email(xml) for xml in MALFORMED_REPORTS] + [good]
        conn = imap_mock.return_value
        conn.search.return_value = (
            "OK",
            [b" ".join(b"%d" % (i + 1) for i in range(len(messages)))],
        )
        conn.fetch.side_effect = [
            ("OK", [(b"%d (RFC822)" % (i + 1), msg), b")"])
            for i, msg in enumerate(messages)
        ]
        call_command("import_aggregated_report", "--imap", stdout=io.StringIO())
        self.assertEqual(conn.fetch.call_count, len(messages))
        self.assertTrue(models.Report.objects.filter(report_id="5672770").exists())
