"""Tests for the migrate_imap_separator command."""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.dovecot import DoveadmError
from modoboa.lib.tests import ModoTestCase
from modoboa.webmail.management.commands.migrate_imap_separator import (
    convert_sieve_script,
)

SCRIPT = """require ["fileinto", "copy", "imap4flags"];
# Archives.2024 stays as is in comments
if header :contains "subject" "invoice" {
    fileinto "Administratif.Factures";
}
if header :contains "from" "list@example.com" {
    fileinto :copy :flags "\\\\Seen" "Lists.Dev.Python";
    stop;
}
if true {
    fileinto "Junk";
}
"""


class ConvertSieveScriptTestCase(SimpleTestCase):
    def test_convert(self):
        script, changed = convert_sieve_script(SCRIPT)
        self.assertIn('fileinto "Administratif/Factures";', script)
        self.assertIn('fileinto :copy :flags "\\\\Seen" "Lists/Dev/Python";', script)
        self.assertIn('fileinto "Junk";', script)
        self.assertIn("# Archives.2024 stays as is in comments", script)
        self.assertEqual(changed, ["Administratif.Factures", "Lists.Dev.Python"])

    def test_nothing_to_convert(self):
        script = 'require ["fileinto"];\nfileinto "Archives/2024";\n'
        self.assertEqual(convert_sieve_script(script), (script, []))


class MigrateImapSeparatorTestCase(ModoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")
        cls.user.parameters.set_values(
            {"sent_folder": "INBOX.Sent", "trash_folder": "Trash"}, app="webmail"
        )
        cls.user.save()

    def setUp(self):
        super().setUp()
        self.backend = mock.Mock()
        self.backend.list_sieve_scripts.side_effect = lambda user: (
            ["modoboa", "other"] if user == "user@test.com" else []
        )
        self.backend.get_sieve_script.side_effect = lambda user, name: (
            SCRIPT if name == "modoboa" else 'fileinto "Junk";'
        )
        patcher = mock.patch(
            "modoboa.webmail.management.commands.migrate_imap_separator."
            "get_dovecot_backend",
            return_value=self.backend,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _folder(self, parameter):
        # A new instance: parameters are loaded once, by the constructor
        user = core_models.User.objects.get(pk=self.user.pk)
        return user.parameters.get_value(parameter, app="webmail")

    def _call(self, *args):
        out = StringIO()
        call_command("migrate_imap_separator", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_migrate(self):
        output = self._call()
        self.backend.put_sieve_script.assert_called_once()
        user, name, script = self.backend.put_sieve_script.call_args.args
        self.assertEqual((user, name), ("user@test.com", "modoboa"))
        self.assertIn('fileinto "Administratif/Factures";', script)
        self.assertEqual(self._folder("sent_folder"), "INBOX/Sent")
        self.assertEqual(self._folder("trash_folder"), "Trash")
        self.assertIn("user@test.com: Sieve script 'modoboa'", output)
        self.assertIn("sent_folder=INBOX/Sent", output)
        # Running it again changes nothing
        self.backend.reset_mock()
        self.backend.get_sieve_script.side_effect = lambda user, name: script
        self._call()
        self.backend.put_sieve_script.assert_not_called()

    def test_dry_run(self):
        output = self._call("--dry-run")
        self.backend.put_sieve_script.assert_not_called()
        self.assertEqual(self._folder("sent_folder"), "INBOX.Sent")
        self.assertIn("Lists.Dev.Python", output)

    def test_clear_cached_separator(self):
        with mock.patch(
            "modoboa.webmail.management.commands.migrate_imap_separator.cache"
        ) as cache_mock:
            self._call()
        keys = cache_mock.delete_many.call_args.args[0]
        self.assertEqual(
            len(keys), core_models.User.objects.filter(mailbox__isnull=False).count()
        )

    def test_doveadm_failure(self):
        self.backend.list_sieve_scripts.side_effect = DoveadmError("boom")
        with self.assertRaises(CommandError):
            self._call()
        # Other accounts and settings are still migrated
        self.assertEqual(self._folder("sent_folder"), "INBOX/Sent")
