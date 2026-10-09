"""Management command tests."""

import os
import shutil
from unittest import mock

from django.test import override_settings
from django.urls import reverse

from modoboa.admin import jobs
from modoboa.lib.tests import ModoAPITestCase
from .. import factories, models


@override_settings(DOVECOT_LOOKUP_PATH=[f"{os.path.dirname(__file__)}/dovecot"])
class MailboxOperationTestCase(ModoAPITestCase):
    """Test management command."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def setUp(self):
        """Initiate test env."""
        super().setUp()
        path = f"{self.workdir}/test.com/admin"
        os.makedirs(path)
        self.set_global_parameter("handle_mailboxes", True)
        self.set_global_parameter("enable_admin_limits", False, app="limits")

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_delete_account(self, mail_home_mock):
        """Check delete operation."""
        path = f"{self.workdir}/test.com/admin"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        mb = models.Mailbox.objects.select_related("user").get(
            address="admin", domain__name="test.com"
        )
        self.client.post(
            reverse("v2:account-delete", args=[mb.user.pk]), {}, format="json"
        )
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertFalse(os.path.exists(mb.mail_home))

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_rename_account(self, mail_home_mock):
        """Check rename operation."""
        path = f"{self.workdir}/test.com/admin"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        mb = models.Mailbox.objects.select_related("user").get(
            address="admin", domain__name="test.com"
        )
        values = {
            "username": "admin2@test.com",
            "role": "DomainAdmins",
            "is_active": True,
            "email": "admin2@test.com",
            "language": "en",
            "mailbox": {"use_domain_quota": True},
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[mb.user.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        path = f"{self.workdir}/test.com/admin2"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertTrue(os.path.exists(mb.mail_home))

    def _rename_admin(self, mail_home_mock):
        """Rename admin@test.com to admin2@test.com and point mail_home to the new path."""
        mail_home_mock.__get__ = mock.Mock(
            return_value=f"{self.workdir}/test.com/admin"
        )
        mb = models.Mailbox.objects.get(address="admin", domain__name="test.com")
        values = {
            "username": "admin2@test.com",
            "role": "DomainAdmins",
            "is_active": True,
            "email": "admin2@test.com",
            "language": "en",
            "mailbox": {"use_domain_quota": True},
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[mb.user.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        new_path = f"{self.workdir}/test.com/admin2"
        mail_home_mock.__get__ = mock.Mock(return_value=new_path)
        return mb, new_path

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_rename_account_destination_exists(self, mail_home_mock):
        """Existing destination: no move, alarm raised, mailbox unblocked."""
        mb, new_path = self._rename_admin(mail_home_mock)
        os.makedirs(new_path)
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertTrue(os.path.exists(f"{self.workdir}/test.com/admin"))
        self.assertFalse(os.path.exists(f"{new_path}/admin"))
        self.assertTrue(
            models.Alarm.objects.filter(
                mailbox=mb, internal_name="mailbox_rename_failed"
            ).exists()
        )

    @mock.patch("modoboa.admin.jobs.exec_cmd", return_value=(1, b"Permission denied"))
    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_rename_account_move_fails(self, mail_home_mock, exec_cmd_mock):
        """Failed move: alarm raised and mailbox unblocked."""
        mb, new_path = self._rename_admin(mail_home_mock)
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        alarm = models.Alarm.objects.get(
            mailbox=mb, internal_name="mailbox_rename_failed"
        )
        self.assertIn("Permission denied", alarm.title)

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_pending_operations_purged_when_disabled(self, mail_home_mock):
        """Disabling handle_mailboxes drops pending operations."""
        self._rename_admin(mail_home_mock)
        self.assertTrue(models.MailboxOperation.objects.exists())
        self.set_global_parameter("handle_mailboxes", False)
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertTrue(os.path.exists(f"{self.workdir}/test.com/admin"))

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_delete_domain(self, mail_home_mock):
        """Check delete operation."""
        path = f"{self.workdir}/test.com/admin"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        domain = models.Domain.objects.get(name="test.com")
        self.client.post(
            reverse("v2:domain-delete", args=[domain.pk]), {}, format="json"
        )
        jobs.handle_mailbox_operations()
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertFalse(os.path.exists(path))
