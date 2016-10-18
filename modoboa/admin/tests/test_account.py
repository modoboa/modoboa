# coding: utf-8

from unittest import skipIf

from django.core.urlresolvers import reverse
from django.test import override_settings

from modoboa.core import factories as core_factories
from modoboa.core import tests as core_tests
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase
from modoboa.lib.tests import NO_LDAP

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

        values.update({"username": "pouet@test.com"})
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        mb = models.Mailbox.objects.get(pk=mb.pk)
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

    def test_delete_default_superadmin(self):
        """Delete default superadmin."""
        sadmin2 = core_factories.UserFactory(
            username="admin2", is_superuser=True)
        sadmin = User.objects.get(username="admin")
        self.client.force_login(sadmin2)
        self.ajax_post(
            reverse("admin:account_delete", args=[sadmin.pk]), {}
        )
        values = {
            "username": "user@test.com", "role": "DomainAdmins",
            "is_active": True, "email": "user@test.com"
        }
        account = User.objects.get(username="user@test.com")
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values
        )

    def test_sender_address(self):
        """Check if sender addresses are saved."""
        account = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "first_name": "Tester",
            "last_name": "Toto", "role": "SimpleUsers",
            "quota_act": True, "is_active": True, "email": "user@test.com",
            "senderaddress": "test@titi.com", "senderaddress_1": "toto@go.com"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values)
        self.assertEqual(
            models.SenderAddress.objects.filter(
                mailbox__address="user").count(),
            2)
        del values["senderaddress_1"]
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values)
        self.assertEqual(
            models.SenderAddress.objects.filter(
                mailbox__address="user").count(),
            1)

    def test_conflicts(self):
        """Check if unicity constraints are respected."""
        values = {
            "username": "user@test.com",
            "password1": "Toto1234", "password2": "Toto1234",
            "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "user@test.com",
            "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values, status=400)

        values.update({"username": "fakeuser@test.com",
                       "email": "fakeuser@test.com"})
        self.ajax_post(reverse("admin:account_add"), values)
        account = User.objects.get(username="fakeuser@test.com")
        values = {
            "username": "user@test.com",
            "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "user@test.com",
        }
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values,
            status=400
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

    def test_account_detail_view(self):
        """Test account detail view."""
        parameters.save_admin(
            "ENABLE_ADMIN_LIMITS", "no", app="limits")
        account = User.objects.get(username="admin@test.com")
        url = reverse("admin:account_detail", args=[account.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Summary", response.content)
        self.assertIn("Administered domains", response.content)
        self.assertNotIn("Resources usage", response.content)
        parameters.save_admin(
            "ENABLE_ADMIN_LIMITS", "yes", app="limits")
        response = self.client.get(url)
        self.assertIn("Resources usage", response.content)


@skipIf(NO_LDAP, "No ldap module installed")
@override_settings(AUTHENTICATION_BACKENDS=(
    'modoboa.lib.authbackends.LDAPBackend',
    'modoboa.lib.authbackends.SimpleBackend',
))
class LDAPAccountTestCase(core_tests.LDAPTestCaseMixin, ModoTestCase):
    """Check LDAP related code."""

    def test_autocreate_disabled(self):
        """Check if objects are not created as expected."""
        self.activate_ldap_authentication()
        self.searchbind_mode()
        parameters.save_admin("AUTO_CREATE_DOMAIN_AND_MAILBOX", "no")
        username = "testuser@example.com"
        self.authenticate(username, "test")
        self.assertFalse(
            models.Domain.objects.filter(name="example.com").exists())
        self.assertFalse(
            models.Mailbox.objects.filter(address="testuser").exists())


class PermissionsTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        from modoboa.lib import parameters
        from modoboa.limits import utils as limits_utils

        super(PermissionsTestCase, cls).setUpTestData()
        for name, tpl in limits_utils.get_user_limit_templates():
            parameters.save_admin(
                "DEFLT_USER_{0}_LIMIT".format(name.upper()), 2,
                app="limits"
            )
        factories.populate_database()
        cls.reseller = core_factories.UserFactory(username="reseller")
        cls.reseller.role = "Resellers"
        cls.user = User.objects.get(username="user@test.com")
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
        self.assertEqual(self.user.role, "DomainAdmins")

        self.values["role"] = "SimpleUsers"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertNotEqual(
            self.user.groups.first().name, "DomainAdmins")

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
        values = {
            "username": "admin@test.com", "first_name": "Admin",
            "password1": "", "password2": "",
            "quota": 10, "is_active": True, "email": "admin@test.com"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[admin.id]),
            values
        )
        self.assertEqual(admin.role, "DomainAdmins")
        self.assertTrue(admin.can_access(
            models.Domain.objects.get(name="test.com")))

        values["role"] = "SuperAdmins"
        self.ajax_post(
            reverse("admin:account_change", args=[admin.id]),
            values
        )
        admin.refresh_from_db()
        self.assertEqual(admin.role, "DomainAdmins")

        self.client.logout()
        self.client.login(username=self.reseller.username, password="toto")
        self.assertTrue(self.reseller.can_access(self.reseller))
        values = {
            "username": self.reseller.username, "first_name": "Reseller",
            "password1": "", "password2": "",
            "is_active": True
        }
        self.ajax_post(
            reverse("admin:account_change", args=[self.reseller.pk]),
            values
        )
        self.assertEqual(self.reseller.role, "Resellers")
        values["role"] = "SuperAdmins"
        self.ajax_post(
            reverse("admin:account_change", args=[self.reseller.pk]),
            values
        )
        self.assertEqual(self.reseller.role, "Resellers")

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
        self.ajax_post(reverse("admin:alias_add"), values)

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

    def test_domadmins_permissions(self):
        """
        Check that two domain admins in the same domains see the same
        content.
        """
        dom = models.Domain.objects.get(name="test.com")
        mb = factories.MailboxFactory(
            domain=dom, address="admin2",
            user__username="admin2@test.com", user__groups=('DomainAdmins', ),
            user__password="{PLAIN}toto")
        dom.add_admin(mb.user)
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test.com", password="toto"))
        values = {
            "username": "new@test.com", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "new@test.com", "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values)

        new_mb = models.Mailbox.objects.get(user__username="new@test.com")
        self.assertTrue(mb.user.can_access(new_mb))
