from unittest import skipIf

from django.test import override_settings
from django.urls import reverse

from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.core.tests import test_ldap
from modoboa.lib.tests import NO_LDAP, ModoTestCase
from modoboa.limits import utils as limits_utils
from .. import factories, models


class AuthenticationTestCase(ModoTestCase):
    """Check authentication."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(AuthenticationTestCase, cls).setUpTestData()
        cls.mb = factories.MailboxFactory(
            domain__name="test.com", address="user",
            user__username="user@test.com",
            user__groups=("SimpleUsers",)
        )

    def test_authentication_unicode(self):
        """Test with unicode password."""
        self.client.logout()
        password = "Tété1234"
        self.mb.user.set_password(password)
        self.mb.user.save(update_fields=["password"])
        data = {"username": self.mb.full_address, "password": password}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:user_index")))


class AccountTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(AccountTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_crud(self):
        values = {
            "username": "tester@test.com", "first_name": "Tester",
            "last_name": "Toto", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "tester@test.com", "stepid": "step2"
        }
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

        values.update({
            "username": "pouet@test.com", "language": "en",
            "secondary_email": "homer@simpson.com",
            "phone_number": "+33612345678"
        })
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        account.refresh_from_db()
        self.assertEqual(account.secondary_email, values["secondary_email"])
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

    @override_settings(LANGUAGE_CODE="fr")
    def test_create_account_default_lang(self):
        """Check if default language is applied."""
        values = {
            "username": "tester@test.com",
            "first_name": "Tester",
            "last_name": "Toto",
            "password1": "Toto1234",
            "password2": "Toto1234",
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": True,
            "email": "tester@test.com",
            "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values)
        account = User.objects.get(username=values["username"])
        self.assertEqual(account.language, "fr")

    def test_forward_updated_on_edit(self):
        account = User.objects.get(username="user@test.com")
        forward = models.Alias.objects.create(address=account.email, internal=False)
        values = {
            "username": "user@test.com",
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": False,
            "email": "user@test.com",
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        forward.refresh_from_db()
        self.assertFalse(forward.enabled)
        values["is_active"] = True
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]), values
        )
        forward.refresh_from_db()
        self.assertTrue(forward.enabled)

    def test_aliases_update_on_rename(self):
        """Check if aliases are updated on mailbox rename."""
        account = User.objects.get(username="user@test.com")
        values = {
            "username": "new_user@test.com",
            "first_name": account.first_name,
            "last_name": account.last_name,
            "role": account.role,
            "quota_act": True,
            "is_active": account.is_active,
            "email": "new_user@test.com",
            "language": "en",
            "create_alias_with_old_address": False,
            "aliases_1": "alias@test.com"
        }
        url = reverse("admin:account_change", args=[account.pk])
        self.ajax_post(url, values)
        qset = account.mailbox.aliasrecipient_set.filter(alias__internal=False)
        for alr in qset:
            self.assertEqual(alr.address, values["email"])

    def test_create_alias_on_rename(self):
        """Check if alias is automatically created."""
        account = User.objects.get(username="user@test.com")
        values = {
            "username": "new_user@test.com",
            "first_name": account.first_name,
            "last_name": account.last_name,
            "role": account.role,
            "quota_act": True,
            "is_active": account.is_active,
            "email": "new_user@test.com",
            "language": "en",
            "create_alias_with_old_address": False
        }
        url = reverse("admin:account_change", args=[account.pk])
        # Rename while option is set to False -> no alias created
        self.ajax_post(url, values)
        self.assertFalse(
            models.AliasRecipient.objects.filter(
                address="new_user@test.com", alias__address="user@test.com",
                alias__internal=False
            ).exists()
        )
        # Now rename while option set to True -> alias created
        values.update({
            "username": "user@test.com",
            "email": "user@test.com",
            "create_alias_with_old_address": True}
        )
        self.ajax_post(url, values)
        self.assertTrue(
            models.AliasRecipient.objects.filter(
                address="user@test.com", alias__address="new_user@test.com",
                alias__internal=False
            ).exists()
        )
        # Change domain while option set to True -> alias created
        values.update({
            "username": "new_user@test2.com",
            "email": "new_user@test2.com",
        })
        self.ajax_post(url, values)
        self.assertTrue(
            models.AliasRecipient.objects.filter(
                address="new_user@test2.com",
                alias__address="user@test.com",
                alias__domain__name="test.com",
                alias__internal=False
            ).exists()
        )

    def test_password_constraints(self):
        """Check password constraints."""
        values = {
            "username": "tester@test.com",
            "first_name": "Tester", "last_name": "Toto",
            "password1": "", "password2": "",
            "role": "SimpleUsers",
            "quota_act": True, "is_active": True, "email": "tester@test.com",
            "stepid": "step2"
        }
        resp = self.ajax_post(reverse("admin:account_add"), values, 400)
        self.assertEqual(
            resp["form_errors"]["password1"][0],
            "This field is required.")
        values["password1"] = "Toto1234"
        values["password2"] = "Toto12345"
        resp = self.ajax_post(reverse("admin:account_add"), values, 400)
        self.assertEqual(
            resp["form_errors"]["password2"][0],
            "The two password fields didn't match.")

        values["password1"] = "toto1234"
        values["password2"] = "toto1234"
        resp = self.ajax_post(reverse("admin:account_add"), values, 400)
        self.assertEqual(
            resp["form_errors"]["password2"][0],
            "Password must contain at least 1 uppercase letter.")

    def test_random_password(self):
        """Try to create an account with a random password."""
        values = {
            "username": "tester@test.com",
            "first_name": "Tester", "last_name": "Toto",
            "random_password": True, "role": "SimpleUsers",
            "quota_act": True, "is_active": True, "email": "tester@test.com",
            "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values)

        account = User.objects.get(username=values["username"])
        password = account.password
        values["language"] = "en"
        # Since 'random_password' is still True, a new password should
        # be generated
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values
        )
        account.refresh_from_db()
        self.assertNotEqual(password, account.password)
        password = account.password

        values["random_password"] = False
        self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values
        )
        account.refresh_from_db()
        self.assertEqual(password, account.password)

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
            "is_active": True, "email": "user@test.com",
            "language": "en"
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
            "senderaddress": "test@titi.com", "senderaddress_1": "toto@go.com",
            "language": "en"
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

    def test_sender_address_as_domainadmin(self):
        """Check that restrictions are applied."""
        admin = User.objects.get(username="admin@test.com")
        self.client.force_login(admin)
        account = User.objects.get(username="user@test.com")
        values = {
            "username": "user@test.com", "first_name": "Tester",
            "last_name": "Toto", "role": "SimpleUsers",
            "quota_act": True, "is_active": True, "email": "user@test.com",
            "senderaddress": "test@titi.com",
            "senderaddress_1": "toto@test2.com"
        }
        response = self.ajax_post(
            reverse("admin:account_change", args=[account.pk]), values, 400)
        self.assertEqual(
            response["form_errors"]["senderaddress_1"][0],
            "You don't have access to this domain")

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
        values = {
            "username": "téster@test.com", "first_name": "Tester",
            "last_name": "Toto", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "quota_act": True,
            "is_active": True, "email": "téster@test.com", "stepid": "step2"
        }
        self.ajax_post(reverse("admin:account_add"), values)

    def _set_quota(self, email, value, expected_status=200):
        account = User.objects.get(username=email)
        values = {
            "username": email, "role": "SimpleUsers", "quota_act": False,
            "is_active": True, "quota": value, "email": email,
            "language": "en"
        }
        self.ajax_post(
            reverse("admin:account_change", args=[account.id]),
            values, status=expected_status
        )

    def test_set_nul_quota_as_superadmin(self):
        self._set_quota("user@test.com", 0)

    def test_set_nul_quota_as_domainadmin(self):
        """Check cases where a domain admin set unlimited quota."""
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test.com", password="toto")
        )
        # Fails because domain has a quota
        self._set_quota("user@test.com", 0, 400)
        self.client.logout()
        self.assertTrue(
            self.client.login(username="admin@test2.com", password="toto")
        )
        # Ok because domain has no quota
        self._set_quota("user@test2.com", 0)

    def test_domain_quota(self):
        """Check domain quota."""
        dom = models.Domain.objects.get(name="test.com")
        dom.quota = 100
        dom.save(update_fields=["quota"])
        # 2 x 10MB
        self.assertEqual(dom.allocated_quota, 20)
        self._set_quota("user@test.com", 80)
        del dom.allocated_quota
        # 10 + 80 < 100 => ok
        self.assertEqual(dom.allocated_quota, 90)
        # 30 + 80 > 100 => failure
        self._set_quota("admin@test.com", 30, 400)

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
        self.set_global_parameter("enable_admin_limits", False, app="limits")
        account = User.objects.get(username="admin@test.com")
        url = reverse("admin:account_detail", args=[account.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Summary", response.content.decode())
        self.assertIn("Administered domains", response.content.decode())
        self.assertNotIn("Resources usage", response.content.decode())
        self.set_global_parameter("enable_admin_limits", True, app="limits")
        response = self.client.get(url)
        self.assertIn("Resources usage", response.content.decode())

    def test_quota_list_view(self):
        """Test quota list view."""
        models.Quota.objects.filter(username="user@test.com").update(
            bytes=5 * 1048576)
        url = reverse("admin:identity_quota_list")
        response = self.ajax_get(url)
        self.assertIn("5M", response["rows"])
        self.assertIn('title="50%"', response["rows"])
        self.assertIn("user@test.com", response["rows"])
        old_rows = response["rows"]

        response = self.ajax_get(
            "{}?sort_order=-quota_value__bytes".format(url))
        self.assertNotEqual(old_rows, response["rows"])
        old_rows = response["rows"]

        response = self.ajax_get(
            "{}?sort_order=-quota_usage".format(url))
        self.assertEqual(old_rows, response["rows"])

        response = self.ajax_get(
            "{}?sort_order=-unknown".format(url), status=400)


@skipIf(NO_LDAP, "No ldap module installed")
@override_settings(AUTHENTICATION_BACKENDS=(
    "modoboa.lib.authbackends.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
))
class LDAPAccountTestCase(test_ldap.LDAPTestCaseMixin, ModoTestCase):
    """Check LDAP related code."""

    def test_autocreate_disabled(self):
        """Check if objects are not created as expected."""
        self.activate_ldap_authentication()
        self.searchbind_mode()
        self.set_global_parameter("auto_create_domain_and_mailbox", False)
        username = "testuser@example.com"
        self.authenticate(username, "test")
        self.assertFalse(
            models.Domain.objects.filter(name="example.com").exists())
        self.assertFalse(
            models.Mailbox.objects.filter(address="testuser").exists())


class PermissionsTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(PermissionsTestCase, cls).setUpTestData()
        parameters = {}
        for name, _definition in limits_utils.get_user_limit_templates():
            parameters["deflt_user_{0}_limit".format(name)] = 2
        cls.localconfig.parameters.set_values(parameters, app="limits")
        cls.localconfig.save()
        factories.populate_database()
        cls.reseller = core_factories.UserFactory(username="reseller")
        cls.reseller.role = "Resellers"
        cls.user = User.objects.get(username="user@test.com")

    def setUp(self):
        """Initiate test context."""
        super(PermissionsTestCase, self).setUp()
        self.values = {
            "username": self.user.username, "role": "DomainAdmins",
            "is_active": self.user.is_active, "email": "user@test.com",
            "quota_act": True, "language": "en"
        }

    def tearDown(self):
        self.client.logout()

    def test_domain_admins(self):
        factories.DomainFactory(name="test2.com")

        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertEqual(self.user.role, "DomainAdmins")

        self.values["mailboxes_limit"] = "0"
        self.values["mailbox_aliases_limit"] = "0"
        self.values["domains"] = ""
        self.values["domains_1"] = "test.com"
        self.values["domains_2"] = "test2.com"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertIn(
            self.user, models.Domain.objects.get(name="test.com").admins.all()
        )
        self.assertIn(
            self.user, models.Domain.objects.get(name="test2.com").admins.all()
        )

        del self.values["domains_2"]
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertIn(
            self.user, models.Domain.objects.get(name="test.com").admins.all()
        )
        self.assertNotIn(
            self.user, models.Domain.objects.get(name="test2.com").admins.all()
        )

        self.values["role"] = "SimpleUsers"
        self.ajax_post(
            reverse("admin:account_change", args=[self.user.id]),
            self.values
        )
        self.assertFalse(
            self.user.groups.filter(name="DomainAdmins").exists()
        )
        self.assertNotIn(
            self.user, models.Domain.objects.get(name="test.com").admins.all()
        )

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
            "quota": 10, "is_active": True, "email": "admin@test.com",
            "language": "en"
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
            "is_active": True, "language": "en"
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
            HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertNotEqual(response["Content-Type"], "application/json")

    def test_domainadmin_deletes_superadmin(self):
        """Check domain admins restrictions about super admins

        When a super admin owns a mailbox and a domain admin exists
        for the associated domain, this domain admin must not be able
        to access the super admin.
        """
        values = {
            "username": "superadmin2@test.com", "first_name": "Super",
            "last_name": "Admin", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SuperAdmins", "is_active": True,
            "email": "superadmin2@test.com", "stepid": "step2"
        }
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
        values = {
            "address": "all@test.com",
            "recipients": "user@test.com",
            "recipients_1": "user@test2.com",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)

    def test_domainadmin_master_user(self):
        """Check domain administrator is not allowed to access this feature."""
        values = {
            "username": "user10@test.com", "first_name": "Test",
            "last_name": "Test", "password1": "Toto1234",
            "password2": "Toto1234", "role": "SimpleUsers", "is_active": True,
            "master_user": True, "email": "user10@test.com", "stepid": "step2"
        }
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
            user__username="admin2@test.com", user__groups=("DomainAdmins", ),
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
