"""Management command tests."""

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
