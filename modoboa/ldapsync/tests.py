"""LDAP sync. related tests."""

from unittest import skipIf

from django.conf import settings
from django.core.management import call_command
from django.utils.encoding import force_bytes, force_str

from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import NO_LDAP, ModoTestCase
from modoboa.parameters import tools as param_tools

if not NO_LDAP:
    import ldap
    from . import lib


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPExportTestCase(ModoTestCase):
    """Synchronization related tests."""

    def setUp(self):
        super().setUp()
        self.set_global_parameters({
            "ldap_enable_sync": True,
            "ldap_server_port": settings.LDAP_SERVER_PORT,
            "ldap_sync_bind_dn": "cn=admin,dc=example,dc=com",
            "ldap_sync_bind_password": "test",
            "ldap_sync_account_dn_template": (
                "cn=%(user)s,ou=users,dc=example,dc=com"),
        }, app="core")
        self.config = dict(param_tools.get_global_parameters("core"))
        self.conn = lib.get_connection(self.config)
        self.username = "testldap@test.com"
        self.dn = self.config["ldap_sync_account_dn_template"] % {
            "user": self.username}

    def reset_ldap_directory(self):
        try:
            self.conn.delete_s(self.dn)
        except ldap.NO_SUCH_OBJECT:
            pass

    def test_sync_user(self):
        self.reset_ldap_directory()
        user = core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("SimpleUsers",)
        )
        self.assertTrue(lib.check_if_dn_exists(self.conn, self.dn))

        lib.get_connection(self.config, self.dn, "toto")

        user.last_name = "LDAP Modif"
        user.save()
        lib.get_connection(self.config, self.dn, "toto")

        res = self.conn.search_s(
            force_str(self.dn), ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))")
        )
        self.assertIn(force_bytes(user.last_name), res[0][1]["sn"])

    def test_sync_domainadmin(self):
        self.reset_ldap_directory()
        core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("DomainAdmins", )
        )
        self.assertFalse(lib.check_if_dn_exists(self.conn, self.dn))

    def test_delete_user(self):
        self.reset_ldap_directory()
        user = core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("SimpleUsers",)
        )
        user.delete()
        ldap_record = self.conn.search_s(
            force_str(self.dn), ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))")
        )
        password = ldap_record[0][1]["userPassword"][0].split(b"}")[1]
        self.assertTrue(password.startswith(b"#"))
        with self.assertRaises(ldap.INVALID_CREDENTIALS):
            lib.get_connection(self.config, self.dn, "toto")

        user = core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("SimpleUsers",)
        )
        self.set_global_parameter(
            "ldap_sync_delete_remote_account", True, app="core")
        user.delete()
        self.assertFalse(lib.check_if_dn_exists(self.conn, self.dn))


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPImportTestCase(ModoTestCase):
    """Import related tests."""

    def setUp(self):
        super().setUp()
        self.set_global_parameters({
            "ldap_enable_import": True,
            "ldap_server_port": settings.LDAP_SERVER_PORT,
            "ldap_sync_bind_dn": "cn=admin,dc=example,dc=com",
            "ldap_sync_bind_password": "test",
            "ldap_import_search_base": "ou=users,dc=example,dc=com",
            "ldap_import_search_filter": "(objectClass=person)",
            "ldap_groups_search_base": "ou=groups,dc=example,dc=com",
            "ldap_admin_groups": "admins",
        }, app="core")
        self.config = dict(param_tools.get_global_parameters("core"))
        self.conn = lib.get_connection(self.config)

    def test_import_from_ldap(self):
        """Check management command."""
        call_command("import_from_ldap_directory")
        self.assertTrue(core_models.User.objects.filter(
            username="testuser@example.com").exists())
        admin = core_models.User.objects.get(username="mailadmin@example.com")
        self.assertEqual(admin.role, "DomainAdmins")
