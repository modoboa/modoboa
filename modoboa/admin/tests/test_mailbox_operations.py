"""Management command tests."""

import os
import shutil
import tempfile
from unittest import mock

from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from modoboa.lib.tests import ModoTestCase
from .. import factories, models


@override_settings(DOVECOT_LOOKUP_PATH=[f"{os.path.dirname(__file__)}/dovecot"])
class MailboxOperationTestCase(ModoTestCase):
    """Test management command."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def setUp(self):
        """Initiate test env."""
        super().setUp()
        self.workdir = tempfile.mkdtemp()
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
        self.ajax_post(reverse("admin:account_delete", args=[mb.user.pk]), {})
        call_command("handle_mailbox_operations")
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
            "subject": "test",
            "content": "content",
        }
        self.ajax_post(reverse("admin:account_change", args=[mb.user.pk]), values)
        path = f"{self.workdir}/test.com/admin2"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        call_command("handle_mailbox_operations")
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertTrue(os.path.exists(mb.mail_home))

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_delete_domain(self, mail_home_mock):
        """Check delete operation."""
        path = f"{self.workdir}/test.com/admin"
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        domain = models.Domain.objects.get(name="test.com")
        self.ajax_post(reverse("admin:domain_delete", args=[domain.pk]))
        call_command("handle_mailbox_operations")
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertFalse(os.path.exists(path))
