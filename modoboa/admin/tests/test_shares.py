"""Tests for the cleanup of shared folders (IMAP ACL)."""

from unittest import mock

from django.test import SimpleTestCase

from modoboa.admin import factories, jobs, models
from modoboa.core import models as core_models
from modoboa.lib.dovecot import DoveadmError
from modoboa.lib.tests import ModoTestCase


class SharesCleanupTestCase(ModoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        factories.populate_database()
        models.UserShare.objects.bulk_create(
            [
                models.UserShare(from_user="admin@test.com", to_user="user@test.com"),
                models.UserShare(from_user="user@test2.com", to_user="user@test.com"),
                models.UserShare(from_user="user@test.com", to_user="admin@test.com"),
            ]
        )
        models.AnyoneShare.objects.create(from_user="user@test.com")

    def setUp(self):
        super().setUp()
        patcher = mock.patch("modoboa.admin.handlers.django_rq.get_queue")
        self.enqueue = patcher.start().return_value.enqueue
        self.addCleanup(patcher.stop)

    def test_delete_mailbox(self):
        with self.captureOnCommitCallbacks(execute=True):
            core_models.User.objects.get(username="user@test.com").delete()
        self.assertFalse(
            models.UserShare.objects.filter(from_user="user@test.com").exists()
        )
        self.assertFalse(models.AnyoneShare.objects.exists())
        # Dovecot updates them while the ACL entries are removed
        self.assertEqual(
            models.UserShare.objects.filter(to_user="user@test.com").count(), 2
        )
        job, owners, old, new = self.enqueue.call_args.args
        self.assertEqual(job, jobs.replace_acl_identifier)
        self.assertCountEqual(owners, ["admin@test.com", "user@test2.com"])
        self.assertEqual((old, new), ("user=user@test.com", None))

    def test_delete_mailbox_without_shares(self):
        with self.captureOnCommitCallbacks(execute=True):
            core_models.User.objects.get(username="admin@test2.com").delete()
        self.enqueue.assert_not_called()

    def test_rename_mailbox(self):
        # A former owner of the new address left a share behind
        models.UserShare.objects.create(
            from_user="renamed@test.com", to_user="admin@test2.com"
        )
        mailbox = models.Mailbox.objects.get(address="user", domain__name="test.com")
        mailbox.address = "renamed"
        with self.captureOnCommitCallbacks(execute=True):
            mailbox.save()
        self.assertCountEqual(
            models.UserShare.objects.filter(from_user="renamed@test.com").values_list(
                "to_user", flat=True
            ),
            ["admin@test.com"],
        )
        self.assertTrue(
            models.AnyoneShare.objects.filter(from_user="renamed@test.com").exists()
        )
        job, owners, old, new = self.enqueue.call_args.args
        self.assertCountEqual(owners, ["admin@test.com", "user@test2.com"])
        self.assertEqual((old, new), ("user=user@test.com", "user=renamed@test.com"))

    def test_save_mailbox_without_rename(self):
        mailbox = models.Mailbox.objects.get(address="user", domain__name="test.com")
        with self.captureOnCommitCallbacks(execute=True):
            mailbox.save()
        self.enqueue.assert_not_called()

    def test_rename_domain(self):
        domain = models.Domain.objects.get(name="test.com")
        domain.name = "renamed.com"
        with self.captureOnCommitCallbacks(execute=True):
            domain.save()
        self.assertTrue(
            models.UserShare.objects.filter(
                from_user="admin@renamed.com", to_user="user@test.com"
            ).exists()
        )
        self.assertTrue(
            models.AnyoneShare.objects.filter(from_user="user@renamed.com").exists()
        )
        calls = {call.args[2]: call.args for call in self.enqueue.call_args_list}
        self.assertEqual(calls["user=user@test.com"][3], "user=user@renamed.com")
        self.assertEqual(calls["user=admin@test.com"][3], "user=admin@renamed.com")


class ReplaceAclIdentifierTestCase(SimpleTestCase):
    def setUp(self):
        self.backend = mock.Mock()
        self.backend.list_mailboxes.return_value = [
            "INBOX",
            "Projets",
            "shared",
            "shared/other@test.com/INBOX",
        ]
        self.backend.acl_get.side_effect = lambda owner, mailbox: (
            {"user=bob@test.com": ["lookup", "read"]} if mailbox == "Projets" else {}
        )
        patcher = mock.patch(
            "modoboa.admin.jobs.get_dovecot_backend", return_value=self.backend
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_remove(self):
        jobs.replace_acl_identifier(["alice@test.com"], "user=bob@test.com")
        # Folders shared with the owner are left alone
        self.assertEqual(
            [call.args[1] for call in self.backend.acl_get.call_args_list],
            ["INBOX", "Projets"],
        )
        self.backend.acl_set.assert_not_called()
        self.backend.acl_delete.assert_called_once_with(
            "alice@test.com", "Projets", "user=bob@test.com"
        )

    def test_replace(self):
        jobs.replace_acl_identifier(
            ["alice@test.com"], "user=bob@test.com", "user=robert@test.com"
        )
        self.backend.acl_set.assert_called_once_with(
            "alice@test.com", "Projets", "user=robert@test.com", ["lookup", "read"]
        )
        self.backend.acl_delete.assert_called_once_with(
            "alice@test.com", "Projets", "user=bob@test.com"
        )

    def test_failure(self):
        def list_mailboxes(owner):
            if owner == "alice@test.com":
                raise DoveadmError("boom")
            return ["Projets"]

        self.backend.list_mailboxes.side_effect = list_mailboxes
        with self.assertRaises(DoveadmError):
            jobs.replace_acl_identifier(
                ["alice@test.com", "carol@test.com"], "user=bob@test.com"
            )
        # The other owners are still processed
        self.backend.acl_delete.assert_called_once_with(
            "carol@test.com", "Projets", "user=bob@test.com"
        )
