# -*- coding: utf-8 -*-

"""Management command tests."""

from __future__ import unicode_literals

import os
import shutil
import tempfile

from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from modoboa.lib.tests import ModoTestCase
from .. import factories, models

try:
    # mock is part of the Python (>= 3.3) standard library
    from unittest import mock
except ImportError:
    # fall back to the mock backport
    import mock


@override_settings(
    DOVECOT_LOOKUP_PATH=["{}/dovecot".format(os.path.dirname(__file__))])
class MailboxOperationTestCase(ModoTestCase):
    """Test management command."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(MailboxOperationTestCase, cls).setUpTestData()
        factories.populate_database()

    def setUp(self):
        """Initiate test env."""
        super(MailboxOperationTestCase, self).setUp()
        self.workdir = tempfile.mkdtemp()
        path = "{}/test.com/admin".format(self.workdir)
        os.makedirs(path)
        self.set_global_parameter("handle_mailboxes", True)
        self.set_global_parameter("enable_admin_limits", False, app="limits")

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_delete_account(self, mail_home_mock):
        """Check delete operation."""
        path = "{}/test.com/admin".format(self.workdir)
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        mb = models.Mailbox.objects.select_related("user").get(
            address="admin", domain__name="test.com")
        self.ajax_post(
            reverse("admin:account_delete", args=[mb.user.pk]), {}
        )
        call_command("handle_mailbox_operations")
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertFalse(os.path.exists(mb.mail_home))

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_rename_account(self, mail_home_mock):
        """Check rename operation."""
        path = "{}/test.com/admin".format(self.workdir)
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        mb = models.Mailbox.objects.select_related("user").get(
            address="admin", domain__name="test.com")
        values = {
            "username": "admin2@test.com", "role": "DomainAdmins",
            "is_active": True, "email": "admin2@test.com",
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[mb.user.pk]), values
        )
        path = "{}/test.com/admin2".format(self.workdir)
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        call_command("handle_mailbox_operations")
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertTrue(os.path.exists(mb.mail_home))

    @mock.patch("modoboa.admin.models.Mailbox.mail_home")
    def test_delete_domain(self, mail_home_mock):
        """Check delete operation."""
        path = "{}/test.com/admin".format(self.workdir)
        mail_home_mock.__get__ = mock.Mock(return_value=path)
        domain = models.Domain.objects.get(name="test.com")
        self.ajax_post(reverse("admin:domain_delete", args=[domain.pk]))
        call_command("handle_mailbox_operations")
        self.assertFalse(models.MailboxOperation.objects.exists())
        self.assertFalse(os.path.exists(path))
