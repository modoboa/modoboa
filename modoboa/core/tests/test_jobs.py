"""Tests cases for RQ jobs."""

from dateutil.relativedelta import relativedelta
import httmock
from reversion import revisions as reversion
from reversion.models import Revision, Version

from django.core import mail
from django.core import management
from django.utils import timezone

from modoboa.core import factories, jobs, mocks, models
from modoboa.lib.tests import SimpleModoTestCase
from modoboa.maillog import factories as maillog_factories, models as maillog_models


class JobsTestCase(SimpleModoTestCase):

    def test_clean_logs(self):
        """Check clean_logs job."""
        management.call_command("load_initial_data", "--no-frontend")
        log1 = factories.LogFactory()
        log2 = factories.LogFactory()
        log1.date_created -= relativedelta(years=2)
        log1.save(update_fields=["date_created"])
        maillog_factories.MaillogFactory(date=timezone.now() - relativedelta(days=190))
        maillog_factories.MaillogFactory()
        user = factories.UserFactory(username="revisioned@test.com")
        for _ in range(3):
            with reversion.create_revision():
                user.save()
        Revision.objects.update(date_created=timezone.now() - relativedelta(years=2))
        jobs.clean_logs()
        self.assertFalse(models.Log.objects.filter(pk=log1.pk).exists())
        self.assertTrue(models.Log.objects.filter(pk=log2.pk).exists())
        self.assertEqual(maillog_models.Maillog.objects.count(), 1)
        # Old revisions are purged, but the latest one per object is kept
        self.assertEqual(Version.objects.get_for_object(user).count(), 1)

    def test_communicate_with_public_api(self):
        """Check that job starts fine."""
        with httmock.HTTMock(
            mocks.modo_api_instance_search,
            mocks.modo_api_instance_create,
            mocks.modo_api_instance_update,
            mocks.modo_api_versions,
        ):
            jobs.communicate_with_public_api()
        self.assertEqual(models.LocalConfig.objects.first().api_pk, 100)
        self.assertEqual(len(mail.outbox), 0)
