"""Domain admins must never be able to manage privileged accounts."""

import importlib

from django.apps import apps
from django.urls import reverse

from modoboa.core.models import ObjectAccess, User
from modoboa.lib import permissions
from modoboa.lib.tests import ModoAPITestCase
from .. import factories, models

PASSWORD = "Toto12345!"
NEW_PASSWORD = "Pwned12345!"


class PrivilegedAccountsTestCase(ModoAPITestCase):
    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.domain = models.Domain.objects.get(name="test.com")
        cls.da = User.objects.get(username="admin@test.com")

    def _create_account(self, username, role, mailbox=True, version="v2"):
        data = {"username": username, "role": role, "password": PASSWORD}
        if mailbox:
            if version == "v2":
                data["mailbox"] = {"use_domain_quota": True}
            else:
                data["mailbox"] = {"full_address": username, "quota": 10}
        url = reverse(f"{version}:account-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return User.objects.get(pk=response.json()["pk"])

    def _assert_not_manageable_by_da(self, account):
        self.assertFalse(self.da.can_access(account))
        if hasattr(account, "mailbox"):
            self.assertFalse(self.da.can_access(account.mailbox))
        self.authenticate_user(self.da)
        url = reverse("v2:account-detail", args=[account.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.patch(url, {"password": NEW_PASSWORD}, format="json")
        self.assertEqual(response.status_code, 404)
        response = self.client.patch(url, {"role": "SimpleUsers"}, format="json")
        self.assertEqual(response.status_code, 404)
        url = reverse("v2:account-delete", args=[account.pk])
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 404)
        url = reverse("v2:account-bulk-delete")
        response = self.client.post(url, {"ids": [account.pk]}, format="json")
        self.assertEqual(response.status_code, 404)
        url = reverse("v1:account-detail", args=[account.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        url = reverse("v1:account-password", args=[account.pk])
        response = self.client.put(
            url,
            {"password": PASSWORD, "new_password": NEW_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        account = User.objects.get(pk=account.pk)
        self.assertTrue(account.check_password(PASSWORD))
        self.assertIn(account.role, ["SuperAdmins", "Resellers"])

    def test_create_superadmin_with_mailbox(self):
        account = self._create_account("boss@test.com", "SuperAdmins")
        self.assertEqual(account.email, "boss@test.com")
        self._assert_not_manageable_by_da(account)

    def test_create_reseller_with_mailbox(self):
        account = self._create_account("reseller@test.com", "Resellers")
        self.assertEqual(account.email, "reseller@test.com")
        self._assert_not_manageable_by_da(account)

    def test_create_superadmin_with_mailbox_v1(self):
        account = self._create_account("boss@test.com", "SuperAdmins", version="v1")
        self.assertEqual(account.email, "boss@test.com")
        self._assert_not_manageable_by_da(account)

    def test_create_simple_user_with_mailbox(self):
        """Domain admins still get access to regular accounts."""
        account = self._create_account("simple@test.com", "SimpleUsers")
        self.assertEqual(account.email, "simple@test.com")
        self.assertTrue(self.da.can_access(account))
        self.assertTrue(self.da.can_access(account.mailbox))
        self.authenticate_user(self.da)
        url = reverse("v2:account-detail", args=[account.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_promote_to_superadmin(self):
        account = User.objects.get(username="user@test.com")
        account.set_password(PASSWORD)
        account.save(update_fields=["password"])
        self.assertTrue(self.da.can_access(account))
        account.role = "SuperAdmins"
        self._assert_not_manageable_by_da(account)

    def test_promote_owned_account_to_reseller(self):
        """Ownership is given to a super admin when the owner is outranked."""
        account = User.objects.get(username="user@test.com")
        account.set_password(PASSWORD)
        account.save(update_fields=["password"])
        ObjectAccess.objects.filter(
            content_type__model="user", object_id=account.pk
        ).update(is_owner=False)
        permissions.grant_access_to_object(self.da, account, is_owner=True)
        account.role = "Resellers"
        self.assertEqual(permissions.get_object_owner(account), self.sadmin)
        self._assert_not_manageable_by_da(account)

    def test_legacy_access_is_ignored(self):
        """Access granted before the fix doesn't allow anything."""
        account = self._create_account("boss@test.com", "SuperAdmins")
        permissions.grant_access_to_object(self.da, account)
        permissions.grant_access_to_object(self.da, account.mailbox)
        self.assertFalse(self.da.can_access(account))
        # Access to an outranking account doesn't give access to the
        # objects it owns either.
        domain = factories.DomainFactory(name="other.com")
        permissions.grant_access_to_object(account, domain, is_owner=True)
        self.assertFalse(self.da.can_access(domain))
        self.authenticate_user(self.da)
        url = reverse("v2:account-detail", args=[account.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.patch(url, {"password": NEW_PASSWORD}, format="json")
        self.assertEqual(response.status_code, 404)
        account.refresh_from_db()
        self.assertTrue(account.check_password(PASSWORD))

    def test_migration_revokes_legacy_access(self):
        superadmin = self._create_account("boss@test.com", "SuperAdmins")
        reseller = self._create_account("reseller@test.com", "Resellers")
        simple = User.objects.get(username="user@test.com")
        for account in [superadmin, reseller]:
            permissions.grant_access_to_object(self.da, account)
            permissions.grant_access_to_object(self.da, account.mailbox)
        # The domain admin owns the super admin account
        ObjectAccess.objects.filter(
            content_type__model="user", object_id=superadmin.pk
        ).update(is_owner=False)
        permissions.grant_access_to_object(self.da, superadmin, is_owner=True)

        migration = importlib.import_module(
            "modoboa.admin.migrations.0025_revoke_access_on_privileged_accounts"
        )
        migration.revoke_access_on_privileged_accounts(apps, None)

        for account in [superadmin, reseller]:
            self.assertFalse(
                self.da.objectaccess_set.filter(
                    content_type__model="user", object_id=account.pk
                ).exists()
            )
            self.assertFalse(
                self.da.objectaccess_set.filter(
                    content_type__model="mailbox", object_id=account.mailbox.pk
                ).exists()
            )
        self.assertEqual(permissions.get_object_owner(superadmin), self.sadmin)
        # Access to regular accounts is kept
        self.assertTrue(self.da.can_access(simple))
        self.assertTrue(self.da.can_access(simple.mailbox))
