"""LDAP sync. related tests."""

from __future__ import unicode_literals

from unittest import skipIf

import ldap

from django.utils import six
from django.utils.encoding import force_bytes, force_str

from modoboa.core import factories as core_factories
from modoboa.lib.tests import NO_LDAP, ModoTestCase
from modoboa.parameters import tools as param_tools

from . import lib


@skipIf(NO_LDAP, "No ldap module installed")
class LDAPSyncTestCase(ModoTestCase):
    """Synchronization related tests."""

    def setUp(self):
        super(LDAPSyncTestCase, self).setUp()
        self.set_global_parameters({
            "ldap_enable_sync": True,
            "ldap_server_port": 3389,
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
            tmp_dn = force_bytes(self.dn) if six.PY2 else self.dn
            self.conn.delete_s(tmp_dn)
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
