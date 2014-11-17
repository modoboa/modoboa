from django.core.urlresolvers import reverse
from modoboa.core.models import User
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin.models import (
    Domain, Mailbox
)
from modoboa.extensions.admin import factories


class AccountTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(AccountTestCase, self).setUp()
        factories.populate_database()

    def test_crud(self):
        values = dict(
            username="tester@test.com", first_name="Tester", last_name="Toto",
            password1="toto", password2="toto", role="SimpleUsers",
            quota_act=True,
            is_active=True, email="tester@test.com", stepid='step2'
        )
        self.ajax_post(reverse("admin:account_add"), values)

        account = User.objects.get(username="tester@test.com")
        mb = account.mailbox_set.all()[0]
        self.assertEqual(mb.full_address, "tester@test.com")
        self.assertEqual(mb.quota, 10)
        self.assertEqual(mb.enabled, True)
        self.assertEqual(mb.quota_value.username, "tester@test.com")
        self.assertEqual(account.username, mb.full_address)
        self.assertTrue(account.check_password("toto"))
        self.assertEqual(account.first_name, "Tester")
        self.assertEqual(account.last_name, "Toto")
        self.assertEqual(mb.domain.mailbox_count, 3)

        values["username"] = "pouet@test.com"
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        mb = Mailbox.objects.get(pk=mb.id)
        self.assertEqual(mb.full_address, "pouet@test.com")
        self.assertEqual(mb.quota_value.username, "pouet@test.com")
        self.ajax_post(
            reverse("admin:account_delete", args=[account.id]), {}
        )

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
        self.clt.logout()
        self.assertTrue(self.clt.login(username="admin@test.com", password="toto"))
        self._set_quota("user@test.com", 0, 400)
        self.clt.logout()
        self.assertTrue(self.clt.login(username="admin@test2.com", password="toto"))
        self._set_quota("user@test2.com", 0)


class PermissionsTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(PermissionsTestCase, self).setUp()
        factories.populate_database()
        self.user = User.objects.get(username='user@test.com')
        self.values = dict(
            username=self.user.username, role="DomainAdmins",
            is_active=self.user.is_active, email="user@test.com",
            quota_act=True
        )

    def tearDown(self):
        self.clt.logout()

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
        self.clt.logout()
        self.assertEqual(self.clt.login(username="admin@test.com", password="toto"),
                         True)
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
        self.assertEqual(admin.can_access(Domain.objects.get(name="test.com")), True)

        values["role"] = "SuperAdmins"
        self.ajax_post(
            reverse("admin:account_change", args=[admin.id]),
            values
        )
        admin = User.objects.get(username="admin@test.com")
        self.assertEqual(admin.group, "DomainAdmins")

    def test_domadmin_access(self):
        self.clt.logout()
        self.assertEqual(
            self.clt.login(username="admin@test.com", password="toto"),
            True)
        response = self.clt.get(reverse("admin:domain_list"))
        self.assertEqual(response.status_code, 200)

        response = self.clt.get(
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
            last_name="Admin", password1="toto", password2="toto",
            role="SuperAdmins", is_active=True,
            email="superadmin2@test.com", stepid='step2'
        )
        self.ajax_post(
            reverse("admin:account_add"),
            values
        )
        account = User.objects.get(username="superadmin2@test.com")
        self.clt.logout()
        self.clt.login(username="admin@test.com", password="toto")
        self.ajax_post(
            reverse("admin:account_delete", args=[account.id]), {}, 403
        )

    def test_domainadmin_dlist_local_domain_not_owned(self):
        """Check if a domain admin can use a local mailbox he can't
        access as a recipient in a distribution list"""
        values = dict(
            email="all@test.com",
            recipients="user@test.com",
            recipients_1="user@test2.com",
            enabled=True
        )
        self.ajax_post(reverse("admin:dlist_add"), values)
