"""Tests cases for RQ jobs."""

from modoboa.lib.tests import ModoTestCase

from modoboa.amavis import factories, jobs, models


class JobsTestCase(ModoTestCase):

    databases = "__all__"

    def test_qcleanup(self):
        factories.create_spam("user@test.com", rs="D")
        jobs.qcleanup()
        self.assertEqual(models.Quarantine.objects.count(), 0)
        self.assertEqual(models.Msgs.objects.count(), 0)
        self.assertEqual(models.Maddr.objects.count(), 0)
        self.assertEqual(models.Msgrcpt.objects.count(), 0)
