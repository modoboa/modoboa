"""Test cases for the limits extension."""

from django.urls import reverse

from modoboa.admin.factories import populate_database
from modoboa.admin.models import Alias, Domain, DomainAlias
from modoboa.core.factories import UserFactory
from modoboa.core.models import User
from modoboa.lib import tests as lib_tests
from .. import utils


class PermissionsTestCase(lib_tests.ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        populate_database()

    def test_domainadmin_deletes_reseller(self):
        """Check if a domain admin can delete a reseller.

        Expected result: no.
        """
        values = {
            "username": "reseller@test.com",
            "first_name": "Reseller",
            "last_name": "",
            "password": "Toto1234",
            "role": "Resellers",
            "is_active": True,
            "email": "reseller@test.com",
        }
        url = reverse("v2:account-list")
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)
        account = User.objects.get(username="reseller@test.com")
        admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(admin)
        url = reverse("v2:account-delete", args=[account.id])
        response = self.client.post(url, {"keep_folder": False}, format="json")
        # account is not visible by admin -> 404
        self.assertEqual(response.status_code, 404)


class ResourceTestCase(lib_tests.ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Custom setUpTestData method."""
        super().setUpTestData()
        cls.localconfig.parameters.set_values(
            {"enable_admin_limits": True, "enable_domain_limits": False}
        )
        for name, _definition in utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(f"deflt_user_{name}_limit", 2)
        cls.localconfig.save()
        populate_database()

    def _create_account(self, username, role="SimpleUsers", status=201, **kwargs):
        values = {
            "username": username,
            "first_name": "Tester",
            "last_name": "Toto",
            "password": "Toto1234",
            "role": role,
            "is_active": True,
            "email": username,
            "mailbox": {"use_domain_quota": True},
        }
        values.update(kwargs)
        response = self.client.post(reverse("v2:account-list"), values, format="json")
        self.assertEqual(response.status_code, status)
        return response

    def _create_alias(self, email, rcpt: list | None = None, status=201):
        if rcpt is None:
            rcpt = ["user@test.com"]
        values = {"address": email, "recipients": rcpt, "enabled": True}
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, status)
        return response

    def _create_domain(self, name, status=201, withtpl=False, **kwargs):
        values = {
            "name": name,
            "quota": 100,
            "default_mailbox_quota": 10,
            "type": "domain",
        }
        if withtpl:
            values.update(
                {
                    "domain_admin": {
                        "username": "admin",
                        "with_mailbox": True,
                        "with_aliases": True,
                    }
                }
            )
        values.update(kwargs)
        response = self.client.post(reverse("v2:domain-list"), values, format="json")
        self.assertEqual(response.status_code, status)
        return response

    def _domain_alias_operation(self, optype, domain, name, status=201):
        if optype == "add":
            dom = Domain.objects.get(name=domain)
            values = {"name": name, "target": dom.pk, "enabled": True}
            response = self.client.post(
                reverse("v2:domain_alias-list"), values, format="json"
            )
            self.assertEqual(response.status_code, status)
            return response
        dalias = DomainAlias.objects.get(name=name)
        response = self.client.delete(
            reverse("v2:domain_alias-detail", args=[dalias.pk])
        )
        self.assertEqual(response.status_code, status)

    def _check_limit(self, name, curvalue, maxvalue):
        limit = self.user.userobjectlimit_set.get(name=name)
        self.assertEqual(limit.current_value, curvalue)
        self.assertEqual(limit.max_value, maxvalue)


class DomainAdminTestCase(ResourceTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.user = User.objects.get(username="admin@test.com")
        cls.user.userobjectlimit_set.filter(
            name__in=["mailboxes", "mailbox_aliases"]
        ).update(max_value=2)

    def setUp(self):
        """Test initialization."""
        super().setUp()
        self.authenticate_user(self.user)

    def test_mailboxes_limit(self):
        self._create_account("tester1@test.com")
        self._check_limit("mailboxes", 1, 2)
        self._create_account("tester2@test.com")
        self._check_limit("mailboxes", 2, 2)
        response = self._create_account("tester3@test.com", status=400)
        self.assertEqual(response.json()["mailbox"][0], "Mailboxes: limit reached")
        self._check_limit("mailboxes", 2, 2)
        response = self.client.post(
            reverse(
                "v2:account-delete",
                args=[User.objects.get(username="tester2@test.com").id],
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self._check_limit("mailboxes", 1, 2)

    def test_aliases_limit(self):
        self._create_alias("alias1@test.com")
        self._check_limit("mailbox_aliases", 1, 2)
        self._create_alias("alias2@test.com")
        self._check_limit("mailbox_aliases", 2, 2)
        response = self._create_alias("alias3@test.com", status=400)
        self.assertEqual(
            response.json()["address"][0], "Mailbox aliases: limit reached"
        )
        self._check_limit("mailbox_aliases", 2, 2)
        # Set unlimited value
        self.user.userobjectlimit_set.filter(name="mailbox_aliases").update(
            max_value=-1
        )
        self._create_alias("alias3@test.com")
        self._check_limit("mailbox_aliases", 3, -1)
        response = self.client.delete(
            reverse(
                "v2:alias-detail",
                args=[Alias.objects.get(address="alias2@test.com").id],
            )
        )
        self.assertEqual(response.status_code, 204)
        self._check_limit("mailbox_aliases", 2, -1)

    def test_aliases_limit_through_account_viewset(self):
        user = User.objects.get(username="user@test.com")
        values = {
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "email": user.email,
            "mailbox": {"quota": 10},
            "aliases": [
                "alias1@test.com",
                "alias2@test.com",
            ],
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        Alias.objects.get(address="alias1@test.com")
        self._check_limit("mailbox_aliases", 2, 2)


class ResellerTestCase(ResourceTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.localconfig.parameters.set_value("deflt_user_quota_limit", 1000)
        cls.localconfig.save()
        cls.user = UserFactory(username="reseller", groups=("Resellers",))

    def setUp(self):
        """Test initialization."""
        super().setUp()
        self.authenticate_user(self.user)

    def test_domains_limit(self):
        self._create_domain("domain1.tld")
        self._check_limit("domains", 1, 2)
        self._create_domain("domain2.tld")
        self._check_limit("domains", 2, 2)
        response = self._create_domain("domain3.tld", 403)

        self._check_limit("domains", 2, 2)
        response = self.client.post(
            reverse(
                "v2:domain-delete", args=[Domain.objects.get(name="domain2.tld").id]
            ),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self._check_limit("domains", 1, 2)

    def test_domain_aliases_limit(self):
        self._create_domain("pouet.com")
        self._domain_alias_operation("add", "pouet.com", "domain-alias1.tld")
        self._check_limit("domain_aliases", 1, 2)
        self._domain_alias_operation("add", "pouet.com", "domain-alias2.tld")
        self._check_limit("domain_aliases", 2, 2)
        response = self._domain_alias_operation(
            "add", "pouet.com", "domain-alias3.tld", 400
        )
        self.assertEqual(response.json()["domain"], "Domain aliases: limit reached")
        self._check_limit("domain_aliases", 2, 2)
        self._domain_alias_operation("delete", "pouet.com", "domain-alias2.tld", 204)
        self._check_limit("domain_aliases", 1, 2)

    def test_domain_admins_limit(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        self._check_limit("domain_admins", 1, 2)
        self._create_account("admin2@domain.tld", role="DomainAdmins")
        self._check_limit("domain_admins", 2, 2)
        resp = self._create_account(
            "admin3@domain.tld", role="DomainAdmins", status=400
        )
        self.assertEqual(resp.json()["role"][0], "Invalid choice")
        self._check_limit("domain_admins", 2, 2)

        self.user.userobjectlimit_set.filter(name="mailboxes").update(max_value=3)
        self._create_account("user1@domain.tld")
        user = User.objects.get(username="user1@domain.tld")
        values = {
            "username": user.username,
            "role": "DomainAdmins",
            "is_active": user.is_active,
            "email": user.email,
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["role"][0], "Invalid choice")
        self._check_limit("domain_admins", 2, 2)

    def test_domain_admin_resource_are_empty(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        domadmin = User.objects.get(username="admin1@domain.tld")
        for name in ["mailboxes", "mailbox_aliases"]:
            self.assertEqual(domadmin.userobjectlimit_set.get(name=name).max_value, 0)

    def test_domain_admins_limit_from_domain_tpl(self):
        self.user.userobjectlimit_set.filter(name="domains").update(max_value=3)
        self._create_domain("domain1.tld", withtpl=True)
        self._create_domain("domain2.tld", withtpl=True)
        self._check_limit("domain_admins", 2, 2)
        self._check_limit("domains", 2, 3)
        response = self._create_domain("domain3.tld", withtpl=True, status=403)
        self.assertEqual(response.json()["error"], "Domain admins: limit reached")
        self._check_limit("domain_admins", 2, 2)
        self._check_limit("domains", 2, 3)

    def test_quota(self):
        """Check quota resource."""
        self._create_domain("domain1.tld", withtpl=True, quota=1000)
        response = self._create_domain(
            "domain2.tld", status=403, withtpl=True, quota=1000
        )
        self.assertEqual(response.json()["error"], "Quota: limit reached")
        dom1 = Domain.objects.get(name="domain1.tld")
        url = reverse("v2:domain-detail", args=[dom1.pk])
        values = {
            "name": dom1.name,
            "type": dom1.type,
            "enabled": dom1.enabled,
            "default_mailbox_quota": dom1.default_mailbox_quota,
            "quota": 500,
        }
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 200)

    def test_quota_constraints(self):
        """Check reseller can't define unlimited quota."""
        response = self._create_domain("domain1.tld", 400, quota=0)
        self.assertEqual(
            response.json()["quota"][0], "You can't define an unlimited quota."
        )
        response = self._create_domain("domain1.tld", 400, default_mailbox_quota=0)
        self.assertEqual(
            response.json()["default_mailbox_quota"][0],
            "You can't define an unlimited quota.",
        )

        self.user.userobjectlimit_set.filter(name="quota").update(max_value=0)
        response = self._create_domain("domain2.tld", quota=0)

    def test_quota_propagation(self):
        """Check that quota is applied everywhere."""
        # Try to assign an unlimited quota to an admin
        # See https://github.com/modoboa/modoboa/issues/1223
        self._create_domain("domain1.tld")
        self._create_account(
            "admin@domain1.tld",
            role="DomainAdmins",
            mailbox={"use_domain_quota": False, "quota": 0},
            status=400,
        )

        self._create_domain("domain2.tld", withtpl=True)
        admin = User.objects.get(username="admin@domain2.tld")
        values = {
            "username": admin.username,
            "role": admin.role,
            "is_active": admin.is_active,
            "email": admin.email,
            "resources": [
                {"name": "mailboxes", "max_value": 1},
                {"name": "mailbox_aliases", "max_value": 2},
            ],
            "language": "en",
            "mailbox": {
                "quota": 0,
            },
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[admin.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_reseller_deletes_domain(self):
        """Check if all resources are restored after the deletion."""
        self._create_domain("domain.tld", withtpl=True)
        dom = Domain.objects.get(name="domain.tld")
        url = reverse("v2:domain-delete", args=[dom.id])
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, 204)
        self._check_limit("domains", 0, 2)
        self._check_limit("domain_admins", 1, 2)
        self._check_limit("mailboxes", 0, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_sadmin_removes_ownership(self):
        self._create_domain("domain.tld", withtpl=True)
        dom = Domain.objects.get(name="domain.tld")

        self.authenticate_user(self.sadmin)
        response = self.client.post(
            reverse("v2:domain-remove-administrator", args=[dom.id]),
            {"account": self.user.id},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self._check_limit("domains", 0, 2)
        self._check_limit("domain_admins", 0, 2)
        self._check_limit("mailboxes", 0, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_allocate_from_pool(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")

        # Give 1 mailbox and 2 aliases to the admin -> should work
        values = {
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "email": user.email,
            "resources": [
                {"name": "mailboxes", "max_value": 1},
                {"name": "mailbox_aliases", "max_value": 2},
            ],
            "language": "en",
            "mailbox": {"use_domain_quota": True},
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self._check_limit("mailboxes", 1, 1)
        self._check_limit("mailbox_aliases", 0, 0)

        # Delete the admin -> resources should go back to the
        # reseller's pool
        response = self.client.post(
            reverse("v2:account-delete", args=[user.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, 204)
        self._check_limit("mailboxes", 0, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_restore_resources(self):
        """Give resource to a domain admin and restore them."""
        self._create_domain("domain.tld")
        dom = Domain.objects.get(name="domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")
        values = {
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "email": user.email,
            "resources": [
                {"name": "mailboxes", "max_value": 1},
                {"name": "mailbox_aliases", "max_value": 2},
            ],
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        dom.add_admin(user)

        self.authenticate_user(user)
        self._create_account("user1@domain.tld", mailbox={"quota": 10})
        self._create_alias("alias1@domain.tld", ["user1@domain.tld"])
        self._create_alias("alias2@domain.tld", ["user1@domain.tld"])

        self.authenticate_user(self.user)
        # Delete the admin -> resources should go back to the
        # reseller's pool
        response = self.client.post(
            reverse("v2:account-delete", args=[user.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, 204)
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 2, 2)

    def test_change_role(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")

        # Give 1 mailbox and 2 aliases to the admin -> should work
        values = {
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "email": user.email,
            "resources": [
                {"name": "mailboxes", "max_value": 1},
                {"name": "mailbox_aliases", "max_value": 2},
            ],
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self._check_limit("mailboxes", 1, 1)
        self._check_limit("mailbox_aliases", 0, 0)

        # Change admin role to SimpleUser -> resources should go back
        # to the reseller.
        values = {
            "username": user.username,
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": user.is_active,
            "email": user.email,
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_allocate_too_much(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")

        # Give 2 mailboxes and 3 aliases to the admin -> should fail.
        values = {
            "username": user.username,
            "role": user.role,
            "quota_act": True,
            "is_active": user.is_active,
            "email": user.email,
            "resources": [
                {"name": "mailboxes", "max_value": 2},
                {"name": "mailbox_aliases", "max_value": 3},
            ],
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[user.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 424)
        self.assertEqual(response.json()["error"], "Not enough resources")
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 0, 2)
