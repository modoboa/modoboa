"""Test cases for the limits extension."""

from django.urls import reverse

from modoboa.admin.factories import populate_database
from modoboa.admin.models import Alias, Domain
from modoboa.core.factories import UserFactory
from modoboa.core.models import User
from modoboa.lib import tests as lib_tests
from .. import utils


class PermissionsTestCase(lib_tests.ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(PermissionsTestCase, cls).setUpTestData()
        populate_database()

    def test_domainadmin_deletes_reseller(self):
        """Check if a domain admin can delete a reseller.

        Expected result: no.
        """
        values = {
            "username": "reseller@test.com", "first_name": "Reseller",
            "last_name": "", "password1": "Toto1234", "password2": "Toto1234",
            "role": "Resellers", "is_active": True,
            "email": "reseller@test.com", "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values)
        account = User.objects.get(username="reseller@test.com")
        admin = User.objects.get(username="admin@test.com")
        self.client.force_login(admin)
        resp = self.ajax_post(
            reverse("admin:account_delete", args=[account.id]),
            {}, status=403
        )
        self.assertEqual(resp, "Permission denied")


class ResourceTestCase(lib_tests.ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Custom setUpTestData method."""
        super(ResourceTestCase, cls).setUpTestData()
        cls.localconfig.parameters.set_values({
            "enable_admin_limits": True,
            "enable_domain_limits": False
        })
        for name, _definition in utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2)
        cls.localconfig.save()
        populate_database()

    def _create_account(
            self, username, role="SimpleUsers", status=200, **kwargs):
        values = {
            "username": username, "first_name": "Tester", "last_name": "Toto",
            "password1": "Toto1234", "password2": "Toto1234", "role": role,
            "quota_act": True, "is_active": True, "email": username,
            "stepid": "step2"
        }
        values.update(kwargs)
        return self.ajax_post(
            reverse("admin:account_add"), values, status
        )

    def _create_alias(self, email, rcpt="user@test.com", status=200):
        values = {
            "address": email, "recipients": rcpt, "enabled": True
        }
        return self.ajax_post(
            reverse("admin:alias_add"), values, status
        )

    def _create_domain(self, name, status=200, withtpl=False, **kwargs):
        values = {
            "name": name, "quota": 100, "default_mailbox_quota": 10,
            "create_dom_admin": False, "with_mailbox": True,
            "create_aliases": False, "stepid": "step3", "type": "domain"
        }
        if withtpl:
            values.update({
                "create_dom_admin": True,
                "dom_admin_username": "admin",
                "create_aliases": True
            })
        values.update(kwargs)
        response = self.ajax_post(
            reverse("admin:domain_add"), values, status
        )
        return response

    def _domain_alias_operation(self, optype, domain, name, status=200):
        dom = Domain.objects.get(name=domain)
        values = {
            "name": dom.name, "quota": dom.quota, "enabled": dom.enabled,
            "type": "domain",
            "default_mailbox_quota": dom.default_mailbox_quota,
        }
        aliases = [alias.name for alias in dom.domainalias_set.all()]
        if optype == "add":
            aliases.append(name)
        else:
            aliases.remove(name)
        for cpt, alias in enumerate(aliases):
            fname = "aliases" if not cpt else "aliases_%d" % cpt
            values[fname] = alias
        self.ajax_post(
            reverse("admin:domain_change", args=[dom.id]),
            values, status
        )

    def _check_limit(self, name, curvalue, maxvalue):
        limit = self.user.userobjectlimit_set.get(name=name)
        self.assertEqual(limit.current_value, curvalue)
        self.assertEqual(limit.max_value, maxvalue)


class DomainAdminTestCase(ResourceTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(DomainAdminTestCase, cls).setUpTestData()
        cls.user = User.objects.get(username="admin@test.com")
        cls.user.userobjectlimit_set.filter(
            name__in=["mailboxes", "mailbox_aliases"]).update(max_value=2)

    def setUp(self):
        """Test initialization."""
        super(DomainAdminTestCase, self).setUp()
        self.client.force_login(self.user)

    def test_mailboxes_limit(self):
        self._create_account("tester1@test.com")
        self._check_limit("mailboxes", 1, 2)
        self._create_account("tester2@test.com")
        self._check_limit("mailboxes", 2, 2)
        self._create_account("tester3@test.com", status=403)
        self._check_limit("mailboxes", 2, 2)
        self.ajax_post(
            reverse("admin:account_delete",
                    args=[User.objects.get(username="tester2@test.com").id]),
            {}
        )
        self._check_limit("mailboxes", 1, 2)

    def test_aliases_limit(self):
        self._create_alias("alias1@test.com")
        self._check_limit("mailbox_aliases", 1, 2)
        self._create_alias("alias2@test.com")
        self._check_limit("mailbox_aliases", 2, 2)
        self._create_alias("alias3@test.com", status=403)
        self._check_limit("mailbox_aliases", 2, 2)
        # Set unlimited value
        self.user.userobjectlimit_set.filter(name="mailbox_aliases").update(
            max_value=-1)
        self._create_alias("alias3@test.com")
        self._check_limit("mailbox_aliases", 3, -1)
        self.ajax_post(
            reverse("admin:alias_delete") + "?selection=%d"
            % Alias.objects.get(address="alias2@test.com").id,
            {}
        )
        self._check_limit("mailbox_aliases", 2, -1)

    def test_aliases_limit_through_account_form(self):
        user = User.objects.get(username="user@test.com")
        values = {
            "username": user.username, "role": user.role,
            "is_active": user.is_active, "email": user.email, "quota_act": True,
            "aliases": "alias1@test.com", "aliases_1": "alias2@test.com",
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        Alias.objects.get(address="alias1@test.com")
        self._check_limit("mailbox_aliases", 2, 2)


class ResellerTestCase(ResourceTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(ResellerTestCase, cls).setUpTestData()
        cls.localconfig.parameters.set_value("deflt_user_quota_limit", 1000)
        cls.localconfig.save()
        cls.user = UserFactory(
            username="reseller", groups=("Resellers",)
        )

    def setUp(self):
        """Test initialization."""
        super(ResellerTestCase, self).setUp()
        self.client.force_login(self.user)

    def test_domains_limit(self):
        response = self.client.get(reverse("admin:domain_list"))
        self.assertContains(response, "Domains (0%)")
        self.assertContains(response, "Domain aliases (0%)")
        self._create_domain("domain1.tld")
        self._check_limit("domains", 1, 2)
        self._create_domain("domain2.tld")
        self._check_limit("domains", 2, 2)
        self._create_domain("domain3.tld", 403)
        self._check_limit("domains", 2, 2)
        self.ajax_post(
            reverse("admin:domain_delete",
                    args=[Domain.objects.get(name="domain2.tld").id]),
            {}
        )
        self._check_limit("domains", 1, 2)

    def test_domain_aliases_limit(self):
        self._create_domain("pouet.com")
        self._domain_alias_operation("add", "pouet.com", "domain-alias1.tld")
        self._check_limit("domain_aliases", 1, 2)
        self._domain_alias_operation("add", "pouet.com", "domain-alias2.tld")
        self._check_limit("domain_aliases", 2, 2)
        self._domain_alias_operation(
            "add", "pouet.com", "domain-alias3.tld", 403
        )
        self._check_limit("domain_aliases", 2, 2)
        self._domain_alias_operation(
            "delete", "pouet.com", "domain-alias2.tld")
        self._check_limit("domain_aliases", 1, 2)

    def test_domain_admins_limit(self):
        response = self.client.get(reverse("admin:identity_list"))
        self.assertContains(response, "Domain admins (0%)")
        self.assertContains(response, "Mailboxes (0%)")
        self.assertContains(response, "Mailbox aliases (0%)")

        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        self._check_limit("domain_admins", 1, 2)
        self._create_account("admin2@domain.tld", role="DomainAdmins")
        self._check_limit("domain_admins", 2, 2)
        resp = self._create_account(
            "admin3@domain.tld",
            role="DomainAdmins",
            status=400)
        self.assertEqual(
            resp["form_errors"]["role"][0],
            "Select a valid choice. DomainAdmins is not one of the available "
            "choices."
        )
        self._check_limit("domain_admins", 2, 2)

        self.user.userobjectlimit_set.filter(
            name="mailboxes").update(max_value=3)
        self._create_account("user1@domain.tld")
        user = User.objects.get(username="user1@domain.tld")
        values = {
            "username": user.username, "role": "DomainAdmins",
            "quota_act": True, "is_active": user.is_active,
            "email": user.email, "language": "en"
        }
        resp = self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values, status=400
        )
        self.assertEqual(
            resp["form_errors"]["role"][0],
            "Select a valid choice. DomainAdmins is not one of the available "
            "choices."
        )
        self._check_limit("domain_admins", 2, 2)

    def test_domain_admin_resource_are_empty(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        domadmin = User.objects.get(username="admin1@domain.tld")
        for l in ["mailboxes", "mailbox_aliases"]:
            self.assertEqual(
                domadmin.userobjectlimit_set.get(name=l).max_value, 0
            )

    def test_domain_admins_limit_from_domain_tpl(self):
        self.user.userobjectlimit_set.filter(
            name="domains").update(max_value=3)
        self._create_domain("domain1.tld", withtpl=True)
        self._create_domain("domain2.tld", withtpl=True)
        self._check_limit("domain_admins", 2, 2)
        self._check_limit("domains", 2, 3)
        self._create_domain("domain3.tld", status=200, withtpl=True)
        self._check_limit("domain_admins", 2, 2)
        self._check_limit("domains", 3, 3)

    def test_quota(self):
        """Check quota resource."""
        self._create_domain("domain1.tld", withtpl=True, quota=1000)
        response = self._create_domain(
            "domain2.tld", status=403, withtpl=True, quota=1000)
        self.assertEqual(response, "Quota: limit reached")
        dom1 = Domain.objects.get(name="domain1.tld")
        url = reverse("admin:domain_change", args=[dom1.pk])
        values = {
            "name": dom1.name, "type": dom1.type, "enabled": dom1.enabled,
            "default_mailbox_quota": dom1.default_mailbox_quota,
            "quota": 500
        }
        self.ajax_post(url, values)

    def test_quota_constraints(self):
        """Check reseller can't define unlimited quota."""
        response = self._create_domain("domain1.tld", 400, quota=0)
        self.assertEqual(
            response["form_errors"]["quota"][0],
            "You can't define an unlimited quota.")
        response = self._create_domain(
            "domain1.tld", 400, default_mailbox_quota=0)
        self.assertEqual(
            response["form_errors"]["default_mailbox_quota"][0],
            "You can't define an unlimited quota.")

        self.user.userobjectlimit_set.filter(name="quota").update(max_value=0)
        response = self._create_domain("domain2.tld", quota=0)

    def test_quota_propagation(self):
        """Check that quota is applied everywhere."""
        # Try to assign an unlimited quota to an admin
        # See https://github.com/modoboa/modoboa/issues/1223
        self._create_domain("domain1.tld")
        self._create_account(
            "admin@domain1.tld", role="DomainAdmins",
            quota_act=False, quota=0, status=400)

        self._create_domain("domain2.tld", withtpl=True)
        admin = User.objects.get(username="admin@domain2.tld")
        values = {
            "username": admin.username, "role": admin.role,
            "is_active": admin.is_active, "email": admin.email,
            "mailboxes_limit": 1, "mailbox_aliases_limit": 2,
            "language": "en", "quota_act": False, "quota": 0
        }
        self.ajax_post(
            reverse("admin:account_change", args=[admin.pk]),
            values,
            400
        )

    def test_reseller_deletes_domain(self):
        """Check if all resources are restored after the deletion."""
        self._create_domain("domain.tld", withtpl=True)
        dom = Domain.objects.get(name="domain.tld")
        self.ajax_post(
            reverse("admin:domain_delete", args=[dom.id]),
            {}
        )
        self._check_limit("domains", 0, 2)
        self._check_limit("domain_admins", 1, 2)
        self._check_limit("mailboxes", 0, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_sadmin_removes_ownership(self):
        self._create_domain("domain.tld", withtpl=True)
        dom = Domain.objects.get(name="domain.tld")
        self.client.logout()
        self.client.login(username="admin", password="password")
        self.ajax_get(
            "{0}?domid={1}&daid={2}".format(
                reverse("admin:permission_remove"),
                dom.id, self.user.id
            ), {}
        )
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
            "username": user.username, "role": user.role, "quota_act": True,
            "is_active": user.is_active, "email": user.email,
            "mailboxes_limit": 1, "mailbox_aliases_limit": 2,
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self._check_limit("mailboxes", 1, 1)
        self._check_limit("mailbox_aliases", 0, 0)

        # Delete the admin -> resources should go back to the
        # reseller's pool
        self.ajax_post(
            reverse("admin:account_delete", args=[user.id]),
            {}
        )
        self._check_limit("mailboxes", 0, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_restore_resources(self):
        """Give resource to a domain admin and restore them."""
        self._create_domain("domain.tld")
        dom = Domain.objects.get(name="domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")
        values = {
            "username": user.username, "role": user.role, "quota_act": True,
            "is_active": user.is_active, "email": user.email,
            "mailboxes_limit": 1, "mailbox_aliases_limit": 2,
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        dom.add_admin(user)
        self.client.logout()
        self.client.login(username="admin1@domain.tld", password="Toto1234")
        self._create_account("user1@domain.tld")
        self._create_alias("alias1@domain.tld", "user1@domain.tld")
        self._create_alias("alias2@domain.tld", "user1@domain.tld")
        self.client.logout()
        self.client.login(username="reseller", password="toto")
        # Delete the admin -> resources should go back to the
        # reseller's pool
        self.ajax_post(
            reverse("admin:account_delete", args=[user.id]),
            {}
        )
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 2, 2)

    def test_change_role(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")

        # Give 1 mailbox and 2 aliases to the admin -> should work
        values = {
            "username": user.username, "role": user.role, "quota_act": True,
            "is_active": user.is_active, "email": user.email,
            "mailboxes_limit": 1, "mailbox_aliases_limit": 2,
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self._check_limit("mailboxes", 1, 1)
        self._check_limit("mailbox_aliases", 0, 0)

        # Change admin role to SimpleUser -> resources should go back
        # to the reseller.
        values = {
            "username": user.username, "role": "SimpleUsers",
            "quota_act": True,
            "is_active": user.is_active, "email": user.email,
            "language": "en",
        }
        self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values
        )
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 0, 2)

    def test_allocate_too_much(self):
        self._create_domain("domain.tld")
        self._create_account("admin1@domain.tld", role="DomainAdmins")
        user = User.objects.get(username="admin1@domain.tld")

        # Give 2 mailboxes and 3 aliases to the admin -> should fail.
        values = {
            "username": user.username, "role": user.role, "quota_act": True,
            "is_active": user.is_active, "email": user.email,
            "mailboxes_limit": 2, "mailbox_aliases_limit": 3,
            "language": "en"
        }
        resp = self.ajax_post(
            reverse("admin:account_change", args=[user.id]),
            values, 424
        )
        self.assertEqual(resp, "Not enough resources")
        self._check_limit("mailboxes", 1, 2)
        self._check_limit("mailbox_aliases", 0, 2)
