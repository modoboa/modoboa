"""LDAP sync. related tests."""

import os
import shutil
import tempfile
from unittest import skipIf

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase
from django.utils.encoding import force_bytes, force_str

from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib.exceptions import InternalError
from modoboa.lib.tests import NO_LDAP, ModoTestCase
from modoboa.parameters import tools as param_tools

if not NO_LDAP:
    import ldap
    from . import lib


@skipIf(NO_LDAP, "No ldap module installed")
class AccountDNTestCase(SimpleTestCase):
    """DN building must escape the username to prevent DN injection."""

    template = "uid=%(user)s,ou=users,dc=example,dc=com"

    def test_normal_username(self):
        config = {"ldap_sync_account_dn_template": self.template}
        self.assertEqual(
            lib._account_dn(config, "john"),
            "uid=john,ou=users,dc=example,dc=com",
        )

    def test_username_with_dn_metacharacters_is_escaped(self):
        config = {"ldap_sync_account_dn_template": self.template}
        dn = lib._account_dn(config, "evil,ou=admins")
        # The injected separator must not appear unescaped, and the template
        # suffix must remain the trailing part of the DN.
        self.assertNotIn("evil,ou=admins", dn)
        self.assertTrue(dn.endswith(",ou=users,dc=example,dc=com"))


@skipIf(NO_LDAP, "No ldap module installed")
class DovecotConfFileTestCase(SimpleTestCase):
    """The generated dovecot conf must be protected against injection."""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.workdir)

    def _config(self, **overrides):
        config = {
            "ldap_dovecot_conf_file": os.path.join(self.workdir, "dovecot-ldap.conf"),
            "ldap_secured": "none",
            "ldap_server_address": "localhost",
            "ldap_server_port": 389,
            "ldap_enable_secondary_server": False,
            "ldap_bind_dn": "cn=admin,dc=example,dc=com",
            "ldap_bind_password": "secret",
            "ldap_search_base": "ou=users,dc=example,dc=com",
            "ldap_search_filter": "(mail=%(user)s)",
        }
        config.update(overrides)
        return config

    def test_valid_config(self):
        config = self._config()
        lib.update_dovecot_config_file(config)
        with open(config["ldap_dovecot_conf_file"]) as fp:
            content = fp.read()
        self.assertIn('dn = "cn=admin,dc=example,dc=com"', content)

    def test_newline_in_value(self):
        for name in (
            "ldap_bind_dn",
            "ldap_bind_password",
            "ldap_search_base",
            "ldap_search_filter",
            "ldap_server_address",
        ):
            config = self._config(**{name: "value\nuris = ldap://evil"})
            with self.assertRaises(InternalError):
                lib.update_dovecot_config_file(config)
            self.assertFalse(os.path.exists(config["ldap_dovecot_conf_file"]))

    def test_quote_breakout(self):
        config = self._config(ldap_bind_dn='cn=x" ,dc=com')
        with self.assertRaises(InternalError):
            lib.update_dovecot_config_file(config)
        config = self._config(ldap_bind_password="pass'word")
        with self.assertRaises(InternalError):
            lib.update_dovecot_config_file(config)

    def test_invalid_conf_file_path(self):
        for path in ("relative/path.conf", os.path.join(self.workdir, "no-ext")):
            config = self._config(ldap_dovecot_conf_file=path)
            with self.assertRaises(InternalError):
                lib.update_dovecot_config_file(config)


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPExportTestCase(ModoTestCase):
    """Synchronization related tests."""

    def setUp(self):
        super().setUp()
        self.set_global_parameters(
            {
                "ldap_enable_sync": True,
                "ldap_server_port": settings.LDAP_SERVER_PORT,
                "ldap_sync_bind_dn": "cn=admin,dc=example,dc=com",
                "ldap_sync_bind_password": "test",
                "ldap_sync_account_dn_template": (
                    "cn=%(user)s,ou=users,dc=example,dc=com"
                ),
            },
            app="core",
        )
        self.config = dict(param_tools.get_global_parameters("core"))
        self.conn = lib.get_connection(self.config)
        self.username = "testldap@test.com"
        self.dn = self.config["ldap_sync_account_dn_template"] % {"user": self.username}

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
            groups=("SimpleUsers",),
        )
        self.assertTrue(lib.check_if_dn_exists(self.conn, self.dn))

        lib.get_connection(self.config, self.dn, "toto")

        user.last_name = "LDAP Modif"
        user.save()
        lib.get_connection(self.config, self.dn, "toto")

        res = self.conn.search_s(
            force_str(self.dn),
            ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))"),
        )
        self.assertIn(force_bytes(user.last_name), res[0][1]["sn"])

    def test_sync_domainadmin(self):
        self.reset_ldap_directory()
        core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("DomainAdmins",),
        )
        self.assertFalse(lib.check_if_dn_exists(self.conn, self.dn))

    def test_delete_user(self):
        self.reset_ldap_directory()
        user = core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("SimpleUsers",),
        )
        user.delete()
        ldap_record = self.conn.search_s(
            force_str(self.dn),
            ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))"),
        )
        password = ldap_record[0][1]["userPassword"][0].split(b"}")[1]
        self.assertTrue(password.startswith(b"#"))
        with self.assertRaises(ldap.INVALID_CREDENTIALS):
            lib.get_connection(self.config, self.dn, "toto")

        user = core_factories.UserFactory(
            username=self.username,
            first_name="Test",
            last_name="LDAP",
            groups=("SimpleUsers",),
        )
        self.set_global_parameter("ldap_sync_delete_remote_account", True, app="core")
        user.delete()
        self.assertFalse(lib.check_if_dn_exists(self.conn, self.dn))


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPImportTestCase(ModoTestCase):
    """Import related tests."""

    def setUp(self):
        super().setUp()
        self.set_global_parameters(
            {
                "ldap_enable_import": True,
                "ldap_server_port": settings.LDAP_SERVER_PORT,
                "ldap_sync_bind_dn": "cn=admin,dc=example,dc=com",
                "ldap_sync_bind_password": "test",
                "ldap_import_search_base": "ou=users,dc=example,dc=com",
                "ldap_import_search_filter": "(objectClass=person)",
                "ldap_groups_search_base": "ou=groups,dc=example,dc=com",
                "ldap_admin_groups": "admins",
            },
            app="core",
        )
        self.config = dict(param_tools.get_global_parameters("core"))
        self.conn = lib.get_connection(self.config)

    def test_import_from_ldap(self):
        """Check management command."""
        call_command("import_from_ldap_directory")
        self.assertTrue(
            core_models.User.objects.filter(username="testuser@example.com").exists()
        )
        admin = core_models.User.objects.get(username="mailadmin@example.com")
        self.assertEqual(admin.role, "DomainAdmins")
