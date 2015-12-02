# coding: utf-8

from django.core.urlresolvers import reverse

from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import models


class AccountTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(AccountTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_crud(self):
        values = dict(
            username="tester@test.com", first_name="Tester", last_name="Toto",
            password1="Toto1234", password2="Toto1234", role="SimpleUsers",
            quota_act=True,
            is_active=True, email="tester@test.com", stepid='step2'
        )
        self.ajax_post(reverse("admin:account_add"), values)

        account = User.objects.get(username="tester@test.com")
        mb = account.mailbox
        self.assertEqual(mb.full_address, "tester@test.com")
        self.assertEqual(mb.quota, 10)
        self.assertTrue(mb.enabled)
        self.assertEqual(mb.quota_value.username, "tester@test.com")
        self.assertEqual(account.username, mb.full_address)
        self.assertTrue(account.check_password("Toto1234"))
        self.assertEqual(account.first_name, "Tester")
        self.assertEqual(account.last_name, "Toto")
        self.assertEqual(mb.domain.mailbox_count, 3)
        # Check if self alias has been created
        self.assertTrue(
            models.AliasRecipient.objects.select_related("alias").filter(
                alias__address=mb.full_address, address=mb.full_address,
                alias__internal=True).exists()
        )

        values["username"] = "pouet@test.com"
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        mb = models.Mailbox.objects.get(pk=mb.id)
        self.assertEqual(mb.full_address, "pouet@test.com")
        self.assertEqual(mb.quota_value.username, "pouet@test.com")
        # Check if self alias has been updated
        self.assertTrue(
            models.AliasRecipient.objects.select_related("alias").filter(
                alias__address=mb.full_address, address=mb.full_address,
                alias__internal=True).exists()
        )
        self.ajax_post(
            reverse("admin:account_delete", args=[account.id]), {}
        )
        # Check if self alias has been deleted
        self.assertFalse(
            models.AliasRecipient.objects.select_related("alias").filter(
                alias__address=mb.full_address, address=mb.full_address,
                alias__internal=True).exists()
        )

    def test_utf8_username(self):
        """Create an account with non-ASCII characters."""
        values = dict(
            username="téster@test.com", first_name="Tester", last_name="Toto",
            password1="Toto1234", password2="Toto1234", role="SimpleUsers",
            quota_act=True,
            is_active=True, email="téster@test.com", stepid="step2"
        )
        self.ajax_post(reverse("admin:account_add"), values)

    def _set_quota(self, email, value, expected_status=200):
        account = User.objects.get(username=email)
        values = {
            "username": email, "role": "SimpleUsers", "quota_act": False,
            "is_active": True, "quota": value, "email": email
        }
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]),
            values, status=expected_status
        )

    def test_set_nul_quota_as_superadmin(self):
        self._set_quota("user@test.com", 0)

    def test_set_nul_quota_as_domainadmin(self):
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test.com", password="toto")
        )
        self._set_quota("user@test.com", 0, 400)
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test2.com", password="toto")
        )
        self._set_quota("user@test2.com", 0)

    def test_master_user(self):
        """Validate the master user mode."""
        values = {
            "username": "masteruser", "role": "SuperAdmins",
            "quota_act": False,
            "is_active": True, "master_user": True, "stepid": "step2",
            "password1": "Toto1234", "password2": "Toto1234"
        }
        self.ajax_post(
            reverse("admin:account_add"), values
        )
        self.assertTrue(User.objects.get(username="masteruser").master_user)

        values = {
            "username": "testuser", "role": "DomainAdmins",
            "quota_act": False,
            "is_active": True, "master_user": True, "stepid": "step2",
            "password1": "Toto1234", "password2": "Toto1234"
        }
        self.ajax_post(
            reverse("admin:account_add"), values, status=400
        )


class PermissionsTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(PermissionsTestCase, cls).setUpTestData()
        factories.populate_database()
        cls.user = User.objects.get(username='user@test.com')
        cls.values = dict(
            username=cls.user.username, role="DomainAdmins",
            is_active=cls.user.is_active, email="user@test.com",
            quota_act=True
        )

    def tearDown(self):
        self.client.logout()

    def test_domain_admins(self):
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertEqual(self.user.group, "DomainAdmins")

        self.values["role"] = "SimpleUsers"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertNotEqual(self.user.group, 'DomainAdmins')

    def test_superusers(self):
        self.values["role"] = "SuperAdmins"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertEqual(
            User.objects.get(username="user@test.com").is_superuser, True
        )

        self.values["role"] = "SimpleUsers"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertEqual(User.objects.get(
            username="user@test.com").is_superuser, False)

    def test_self_modif(self):
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test.com", password="toto")
        )
        admin = User.objects.get(username="admin@test.com")
        values = dict(
            username="admin@test.com", first_name="Admin",
            password1="", password2="",
            quota=10, is_active=True, email="admin@test.com"
        )
        self.ajax_post(
            reverse("admin:account_change", args=[admin.id]),
            values
        )
        self.assertEqual(admin.group, "DomainAdmins")
        self.assertTrue(admin.can_access(
            models.Domain.objects.get(name="test.com")))

        values["role"] = "SuperAdmins"
        self.ajax_post(
            reverse("admin:account_change", args=[admin.id]),
            values
        )
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(admin.group, "DomainAdmins")

    def test_domadmin_access(self):
        self.client.logout()
        self.assertEqual(
            self.client.login(username="admin@test.com", password="toto"),
            True)
        response = self.client.get(reverse("admin:domain_list"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse("admin:account_change", args=[self.user.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotEqual(response["Content-Type"], "application/json")

    def test_domainadmin_deletes_superadmin(self):
        """Check domain admins restrictions about super admins

        When a super admin owns a mailbox and a domain admin exists
        for the associated domain, this domain admin must not be able
        to access the super admin.
        """
        values = dict(
            username="superadmin2@test.com", first_name="Super",
            last_name="Admin", password1="Toto1234", password2="Toto1234",
            role="SuperAdmins", is_active=True,
            email="superadmin2@test.com", stepid='step2'
        )
        self.ajax_post(
            reverse("admin:account_add"),
            values
        )
        account = User.objects.get(username="superadmin2@test.com")
        self.client.logout()
        self.client.login(username="admin@test.com", password="toto")
        self.ajax_post(
            reverse("admin:account_delete", args=[account.id]), {}, 403
        )

    def test_domainadmin_dlist_local_domain_not_owned(self):
        """Check if a domain admin can use a local mailbox he can't
        access as a recipient in a distribution list"""
        values = dict(
            address="all@test.com",
            recipients="user@test.com",
            recipients_1="user@test2.com",
            enabled=True
        )
        self.ajax_post(reverse("admin:dlist_add"), values)

    def test_domainadmin_master_user(self):
        """Check domain administrator is not allowed to access this feature."""
        values = dict(
            username="user10@test.com", first_name="Test",
            last_name="Test", password1="Toto1234", password2="Toto1234",
            role="SimpleUsers", is_active=True, master_user=True,
            email="user10@test.com", stepid='step2'
        )
        self.ajax_post(
            reverse("admin:account_add"),
            values, status=400
        )
