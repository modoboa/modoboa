"""Repair command tests"""
from django.core import management

from modoboa.lib.permissions import get_object_owner
from modoboa.lib.permissions import ObjectAccess
from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import models


class RepairTestCase(ModoTestCase):
    """TestCase for repair command."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super(RepairTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_management_command(self):
        """Check that command works fine."""
        ObjectAccess.objects.all().delete()
        mbox = models.Mailbox.objects.all()[0]
        # assert mbox has no owner
        self.assertIs(get_object_owner(mbox), None)
        # fix it. run in quiet mode because we dont want output in tests
        management.call_command("modo", "repair", "--quiet")
        # assert its fixed
        self.assertIsNot(get_object_owner(mbox), None)

    def test_management_command_with_dry_run(self):
        """Check that command works fine."""
        ObjectAccess.objects.all().delete()
        mbox = models.Mailbox.objects.all()[0]
        # assert mbox has no owner
        self.assertIs(get_object_owner(mbox), None)
        # show problems. run in quiet mode because we dont want output in tests
        management.call_command("modo", "repair", "--quiet", "--dry-run")
        # assert its not fixed
        self.assertIs(get_object_owner(mbox), None)

    def test_management_command_with_nul_domain(self):
        """ Just assume nothing raise when an alias has no domain"""
        models.Alias.objects.create(address='@modoboa.xxx')
        management.call_command("modo", "repair", "--quiet")
