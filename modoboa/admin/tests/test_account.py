from unittest import skipIf
import string

from django.test import override_settings
from django.urls import reverse

from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.core.tests import test_ldap
from modoboa.lib.tests import NO_LDAP, ModoAPITestCase
from modoboa.limits import utils as limits_utils
from .. import factories, models, lib


class AuthenticationTestCase(ModoAPITestCase):
    """Check authentication."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.mb = factories.MailboxFactory(
            domain__name="test.com",
            address="user",
            user__username="user@test.com",
            user__groups=("SimpleUsers",),
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
        self.assertEqual(response.url, "/")


class AccountTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_random_password(self):
        # Setting allow_special_characters to False
        self.localconfig.parameters.set_value("allow_special_characters", False, "core")
        random_password_length = self.localconfig.parameters.get_value(
            "random_password_length", "core"
        )
        self.localconfig.save()

        random_password = lib.make_password()
        self.assertEqual(len(random_password), random_password_length)
        self.assertEqual(
            len([char for char in random_password if char in list(string.punctuation)]),
            0,
        )

        # And with allow_special_characters to True
        self.localconfig.parameters.set_value("allow_special_characters", True, "core")
        self.localconfig.save()

        random_password = lib.make_password()
        self.assertEqual(len(random_password), random_password_length)
        self.assertNotEqual(
            len([char for char in random_password if char in list(string.punctuation)]),
            0,
        )

    def test_aliases_update_on_disable(self):
        """Check if aliases are disabled when account is disabled."""
        account = User.objects.get(username="user@test.com")
        internal = models.Alias.objects.get(address=account.email, internal=True)
        forward = models.Alias.objects.create(address=account.email, internal=False)
        factories.AliasRecipientFactory.create(
            address=account.mailbox.full_address,
            alias=forward,
            r_mailbox=account.mailbox,
        )
        values = {
            "username": "user@test.com",
            "role": "SimpleUsers",
            "mailbox": {
                "use_domain_quota": True,
            },
            "is_active": False,
            "email": "user@test.com",
            "language": "en",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[account.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        internal.refresh_from_db()
        self.assertFalse(internal.enabled)
        forward.refresh_from_db()
        self.assertFalse(forward.enabled)
        values["is_active"] = True
        response = self.client.put(
            reverse("v2:account-detail", args=[account.pk]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        internal.refresh_from_db()
        self.assertFalse(internal.enabled)
        forward.refresh_from_db()
        self.assertFalse(forward.enabled)


@skipIf(NO_LDAP, "No ldap module installed")
@override_settings(
    AUTHENTICATION_BACKENDS=(
        "modoboa.lib.authbackends.LDAPBackend",
        "django.contrib.auth.backends.ModelBackend",
    )
)
class LDAPAccountTestCase(test_ldap.LDAPTestCaseMixin, ModoAPITestCase):
    """Check LDAP related code."""

    def test_autocreate_disabled(self):
        """Check if objects are not created as expected."""
        self.activate_ldap_authentication()
        self.searchbind_mode()
        self.set_global_parameter("auto_create_domain_and_mailbox", False)
        username = "testuser@example.com"
        self.authenticate(username, "test")
        self.assertFalse(models.Domain.objects.filter(name="example.com").exists())
        self.assertFalse(models.Mailbox.objects.filter(address="testuser").exists())


class PermissionsTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        parameters = {}
        for name, _definition in limits_utils.get_user_limit_templates():
            parameters[f"deflt_user_{name}_limit"] = 2
        cls.localconfig.parameters.set_values(parameters, app="limits")
        cls.localconfig.save()
        factories.populate_database()
        cls.reseller = core_factories.UserFactory(username="reseller")
        cls.reseller.role = "Resellers"
        cls.user = User.objects.get(username="user@test.com")

    def setUp(self):
        """Initiate test context."""
        super().setUp()
        self.values = {
            "username": self.user.username,
            "role": "DomainAdmins",
            "is_active": self.user.is_active,
            "mailbox": {
                "use_domain_quota": True,
            },
            "language": "en",
        }

    def test_domain_admins(self):
        factories.DomainFactory(name="test2.com")

        response = self.client.put(
            reverse("v2:account-detail", args=[self.user.id]),
            self.values,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.role, "DomainAdmins")

        self.values["resources"] = [
            {"name": "mailboxes", "max_value": 0},
            {"name": "mailbox_aliases", "max_value": 0},
        ]
        response = self.client.put(
            reverse("v2:account-detail", args=[self.user.id]),
            self.values,
            format="json",
        )
        for name in ["test.com", "test2.com"]:
            domain = models.Domain.objects.get(name=name)
            domain.add_admin(self.user)

        self.assertIn(
            self.user, models.Domain.objects.get(name="test.com").admins.all()
        )
        self.assertIn(
            self.user, models.Domain.objects.get(name="test2.com").admins.all()
        )

        self.values["role"] = "SimpleUsers"
        response = self.client.put(
            reverse("v2:account-detail", args=[self.user.id]),
            self.values,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.groups.filter(name="DomainAdmins").exists())
        self.assertNotIn(
            self.user, models.Domain.objects.get(name="test.com").admins.all()
        )

    def test_superusers(self):
        self.values["role"] = "SuperAdmins"
        response = self.client.put(
            reverse("v2:account-detail", args=[self.user.id]),
            self.values,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, True)

        self.values["role"] = "SimpleUsers"
        response = self.client.put(
            reverse("v2:account-detail", args=[self.user.id]),
            self.values,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.get(username="user@test.com").is_superuser, False)

    def test_self_modif(self):
        dadmin = User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        self.assertTrue(dadmin.can_access(models.Domain.objects.get(name="test.com")))

        values = {
            "username": "admin@test.com",
            "first_name": "Admin",
            "role": "DomainAdmins",
            "mailbox": {
                "quota": 10,
            },
            "is_active": True,
            "language": "en",
            "domains": ["test.com"],
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[dadmin.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(dadmin.role, "DomainAdmins")
        self.assertTrue(dadmin.can_access(models.Domain.objects.get(name="test.com")))

        values["role"] = "SuperAdmins"
        response = self.client.put(
            reverse("v2:account-detail", args=[dadmin.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["role"][0], "Invalid choice")

        self.authenticate_user(self.reseller)
        self.assertTrue(self.reseller.can_access(self.reseller))
        values = {
            "username": self.reseller.username,
            "first_name": "Reseller",
            "is_active": True,
            "language": "en",
            "role": "Resellers",
        }
        response = self.client.put(
            reverse("v2:account-detail", args=[self.reseller.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.reseller.role, "Resellers")
        values["role"] = "SuperAdmins"
        response = self.client.put(
            reverse("v2:account-detail", args=[self.reseller.id]), values, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["role"][0], "Invalid choice")

    def test_domainadmin_deletes_superadmin(self):
        """Check domain admins restrictions about super admins

        When a super admin owns a mailbox and a domain admin exists
        for the associated domain, this domain admin must not be able
        to access the super admin.
        """
        values = {
            "username": "superadmin2@test.com",
            "first_name": "Super",
            "last_name": "Admin",
            "password": "Toto1234",
            "role": "SuperAdmins",
            "is_active": True,
        }
        response = self.client.post(reverse("v2:account-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

        account = User.objects.get(username="superadmin2@test.com")
        dadmin = User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        response = self.client.post(
            reverse("v2:account-delete", args=[account.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_domainadmin_dlist_local_domain_not_owned(self):
        """Check if a domain admin can use a local mailbox he can't
        access as a recipient in a distribution list"""
        dadmin = User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        values = {
            "address": "all@test.com",
            "recipients": ["user@test.com", "user@test2.com"],
            "enabled": True,
        }
        response = self.client.post(reverse("v2:alias-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

    def test_domainadmin_master_user(self):
        """Check domain administrator is not allowed to access this feature."""
        dadmin = User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        values = {
            "username": "user10@test.com",
            "first_name": "Test",
            "last_name": "Test",
            "password": "Toto1234",
            "role": "SimpleUsers",
            "is_active": True,
            "master_user": True,
        }
        response = self.client.post(reverse("v2:account-list"), values, format="json")
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="user10@test.com")
        self.assertFalse(user.master_user)

    def test_domadmins_permissions(self):
        """
        Check that two domain admins in the same domain see the same
        content.
        """
        dom = models.Domain.objects.get(name="test.com")
        mb = factories.MailboxFactory(
            domain=dom,
            address="admin2",
            user__username="admin2@test.com",
            user__groups=("DomainAdmins",),
            user__password="{PLAIN}toto",
        )
        dom.add_admin(mb.user)
        dadmin = User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        values = {
            "username": "new@test.com",
            "password": "Toto1234",
            "role": "SimpleUsers",
            "mailbox": {"use_domain_quota": True},
            "is_active": True,
        }
        response = self.client.post(reverse("v2:account-list"), values, format="json")
        self.assertEqual(response.status_code, 201)

        new_mb = models.Mailbox.objects.get(user__username=values["username"])
        self.assertTrue(mb.user.can_access(new_mb))
