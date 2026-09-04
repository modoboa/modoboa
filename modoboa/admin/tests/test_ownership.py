"""Tests about object ownership."""

from django.core import management

from modoboa.core.models import User
from modoboa.lib.permissions import get_object_owner
from modoboa.lib.tests import ModoTestCase
from .. import factories, models


class OwnershipTestCase(ModoTestCase):
    """Check that objects never end up without an owner."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create some data."""
        super().setUpTestData()
        factories.populate_database()

    def _create_super_admin(self, username):
        """Return a new active super admin."""
        account = User(username=username, email=f"{username}@test.com")
        account.set_password("toto")
        account.is_superuser = True
        account.is_active = True
        account.save()
        return account

    def _create_owned_objects(self, creator):
        """Return an account and a mailbox owned by creator."""
        domain = models.Domain.objects.get(name="test.com")
        account = User(username="owned@test.com", email="owned@test.com")
        account.save(creator=creator)
        mbox = models.Mailbox(
            address="owned", domain=domain, user=account, use_domain_quota=True
        )
        mbox.set_quota(override_rules=True)
        mbox.save(creator=creator)
        self.assertEqual(get_object_owner(account), creator)
        self.assertEqual(get_object_owner(mbox), creator)
        return account, mbox

    def test_downgrade_domain_admin_to_simple_user(self):
        """Objects owned by a demoted admin must be given to somebody."""
        admin = User.objects.get(username="admin@test.com")
        account, mbox = self._create_owned_objects(admin)

        admin.role = "SimpleUsers"

        for obj in (account, mbox):
            owner = get_object_owner(obj)
            self.assertIsNotNone(owner)
            self.assertNotEqual(owner, admin)

    def test_downgrade_super_admin(self):
        """Same when a super admin loses its role."""
        sadmin = User.objects.get(username="admin")
        domain = models.Domain.objects.get(name="test.com")
        self.assertEqual(get_object_owner(domain), sadmin)
        self._create_super_admin("other")

        sadmin.role = "DomainAdmins"

        owner = get_object_owner(domain)
        self.assertIsNotNone(owner)
        self.assertNotEqual(owner, sadmin)

    def test_downgrade_transfers_to_own_owner(self):
        """Ownership goes to the account which created the demoted one."""
        sadmin = User.objects.get(username="admin")
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(get_object_owner(admin), sadmin)
        account, mbox = self._create_owned_objects(admin)

        admin.role = "SimpleUsers"

        self.assertEqual(get_object_owner(account), sadmin)
        self.assertEqual(get_object_owner(mbox), sadmin)

    def test_downgrade_keeps_existing_access(self):
        """An object the new owner could already see stays visible once."""
        sadmin = User.objects.get(username="admin")
        admin = User.objects.get(username="admin@test.com")
        account, mbox = self._create_owned_objects(admin)
        # sadmin already has a non owner access on both objects
        self.assertTrue(sadmin.can_access(account))
        self.assertTrue(sadmin.can_access(mbox))

        admin.role = "SimpleUsers"

        for obj in (account, mbox):
            self.assertEqual(get_object_owner(obj), sadmin)
            self.assertEqual(
                sadmin.objectaccess_set.filter(
                    content_type__model=obj.__class__.__name__.lower(),
                    object_id=obj.pk,
                ).count(),
                1,
            )

    def test_promotion_keeps_owners(self):
        """Promoting somebody must not steal ownership."""
        sadmin = User.objects.get(username="admin")
        admin = User.objects.get(username="admin@test.com")
        account, mbox = self._create_owned_objects(sadmin)

        admin.role = "SuperAdmins"

        self.assertEqual(get_object_owner(account), sadmin)
        self.assertEqual(get_object_owner(mbox), sadmin)

    def test_delete_self_owned_admin_without_request(self):
        """The default admin owns itself and is deletable out of a request."""
        sadmin = User.objects.get(username="admin")
        self.assertEqual(get_object_owner(sadmin), sadmin)
        domain = models.Domain.objects.get(name="test.com")
        other = self._create_super_admin("other")

        sadmin.delete()

        self.assertEqual(get_object_owner(domain), other)

    def test_repair_finds_nothing_after_downgrade(self):
        """The repair command must have nothing left to fix."""
        admin = User.objects.get(username="admin@test.com")
        self._create_owned_objects(admin)
        admin.role = "SimpleUsers"

        management.call_command("modo", "repair", "--quiet")

        for model in (models.Domain, models.Mailbox):
            for obj in model.objects.all():
                self.assertIsNotNone(get_object_owner(obj), f"{obj} has no owner")
