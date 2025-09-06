"""Management commands tests."""

from dateutil.relativedelta import relativedelta

from django.core.management import call_command
from django.utils import timezone

from modoboa.lib.tests import ModoTestCase
from .. import factories, models


class ManagementCommandTestCase(ModoTestCase):
    """Management commands tests."""

    databases = "__all__"

    def test_qcleanup(self):
        """Test qcleanup command."""
        factories.create_spam("user@test.com", rs="D")
        call_command("qcleanup")
        self.assertEqual(models.Quarantine.objects.count(), 0)
        self.assertEqual(models.Msgs.objects.count(), 0)
        self.assertEqual(models.Maddr.objects.count(), 0)
        self.assertEqual(models.Msgrcpt.objects.count(), 0)

        factories.create_spam("user@test.com", rs="D")
        msgrcpt = factories.create_spam("user@test.com", rs="R")
        call_command("qcleanup")
        # Should not raise anything
        msgrcpt.refresh_from_db()

        self.set_global_parameter("released_msgs_cleanup", True)
        call_command("qcleanup")
        with self.assertRaises(models.Msgrcpt.DoesNotExist):
            msgrcpt.refresh_from_db()

        msgrcpt = factories.create_spam("user@test.com")
        msgrcpt.mail.time_num = int(
            (timezone.now() - relativedelta(days=40)).strftime("%s")
        )
        msgrcpt.mail.save(update_fields=["time_num"])
        self.set_global_parameter("max_messages_age", 30)
        call_command("qcleanup")
        with self.assertRaises(models.Msgrcpt.DoesNotExist):
            msgrcpt.refresh_from_db()
