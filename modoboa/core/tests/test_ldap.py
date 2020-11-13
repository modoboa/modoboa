"""Tests for core application."""

from unittest import skipIf

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.utils.functional import cached_property

from modoboa.lib import exceptions
from modoboa.lib.tests import NO_LDAP, ModoTestCase
from .. import factories, models


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPTestCaseMixin(object):
    """Set of methods used to test LDAP features."""

    @cached_property
    def ldapauthbackend(self):
        """Return LDAPAuthBackend instance."""
        from modoboa.lib.ldap_utils import LDAPAuthBackend
        return LDAPAuthBackend()

    def activate_ldap_authentication(self):
        """Modify settings."""
        self.set_global_parameters({
            "authentication_type": "ldap",
            "ldap_server_port": settings.LDAP_SERVER_PORT
        })

    def restore_user_password(self, username, new_password):
        """Restore user password to its initial state."""
        for password in ["Toto1234", "test"]:
            try:
                self.ldapauthbackend.update_user_password(
                    username, password, new_password)
            except exceptions.InternalError:
                pass
            else:
                return
        raise RuntimeError("Can't restore user password.")

    def authenticate(self, user, password, restore_before=True):
        """Restore password and authenticate user."""
        self.client.logout()
        if restore_before:
            self.restore_user_password(user, password)
        self.assertTrue(
            self.client.login(username=user, password=password))

    def searchbind_mode(self):
        """Apply settings required by the searchbind mode."""
        self.set_global_parameters({
            "ldap_auth_method": "searchbind",
            "ldap_bind_dn": "cn=admin,dc=example,dc=com",
            "ldap_bind_password": "test",
            "ldap_search_base": "ou=users,dc=example,dc=com"
        })

    def directbind_mode(self):
        """Apply settings required by the directbind mode."""
        self.set_global_parameters({
            "ldap_auth_method": "directbind",
            "ldap_user_dn_template": "cn=%(user)s,ou=users,dc=example,dc=com"
        })


@override_settings(AUTHENTICATION_BACKENDS=(
    "modoboa.lib.authbackends.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend"
))
class LDAPAuthenticationTestCase(LDAPTestCaseMixin, ModoTestCase):
    """Validate LDAP authentication scenarios."""

    def setUp(self):
        """Create test data."""
        super(LDAPAuthenticationTestCase, self).setUp()
        self.activate_ldap_authentication()

    def check_created_user(self, username, group="SimpleUsers", with_mb=True):
        """Check that created user is valid."""
        user = models.User.objects.get(username=username)
        self.assertEqual(user.role, group)
        if with_mb:
            self.assertEqual(user.email, username)
            self.assertEqual(user.mailbox.domain.name, "example.com")
            self.assertEqual(user.mailbox.full_address, username)

    @override_settings(AUTH_LDAP_USER_DN_TEMPLATE=None)
    def test_searchbind_authentication(self):
        """Test the bind&search method."""
        self.searchbind_mode()
        username = "testuser@example.com"
        self.authenticate(username, "test")
        self.check_created_user(username)

        self.set_global_parameters({
            "ldap_admin_groups": "admins",
            "ldap_groups_search_base": "ou=groups,dc=example,dc=com"
        })
        username = "mailadmin@example.com"
        self.authenticate(username, "test", False)
        self.check_created_user(username, "DomainAdmins")

    def test_directbind_authentication(self):
        """Test the directbind method."""
        self.client.logout()
        self.directbind_mode()

        username = "testuser"
        self.client.login(username=username, password="test")
        self.check_created_user(username + "@example.com")

        # 1: must work because usernames of domain admins are not
        # always email addresses
        self.set_global_parameters({
            "ldap_admin_groups": "admins",
            "ldap_groups_search_base": "ou=groups,dc=example,dc=com"
        })
        username = "mailadmin"
        self.authenticate(username, "test", False)
        self.check_created_user("mailadmin@example.com", "DomainAdmins", False)


class ProfileTestCase(LDAPTestCaseMixin, ModoTestCase):
    """Profile related tests."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(ProfileTestCase, cls).setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=("SimpleUsers",)
        )

    @override_settings(AUTHENTICATION_BACKENDS=(
        "modoboa.lib.authbackends.LDAPBackend",
        "django.contrib.auth.backends.ModelBackend"
    ))
    def test_update_password_ldap(self):
        """Update password for an LDAP user."""
        self.activate_ldap_authentication()
        self.searchbind_mode()

        username = "testuser@example.com"
        self.authenticate(username, "test")
        self.ajax_post(
            reverse("core:user_profile"),
            {"language": "en", "oldpassword": "test",
             "newpassword": "Toto1234", "confirmation": "Toto1234"}
        )
        self.authenticate(username, "Toto1234", False)
