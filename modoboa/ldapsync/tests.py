"""LDAP sync. related tests."""

from __future__ import unicode_literals

from unittest import skipIf

import ldap

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

    def test_sync_user(self):
        username = "testldap@test.com"
        dn = self.config["ldap_sync_account_dn_template"] % {
            "user": username}
        try:
            self.conn.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            pass
        user = core_factories.UserFactory(
            username=username,
            first_name="Test",
            last_name="LDAP"
        )
        self.assertTrue(lib.check_if_dn_exists(self.conn, dn))
        user.last_name = "LDAP Modif"
        user.save()

        res = self.conn.search_s(
            force_str(dn), ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))")
        )
        self.assertIn(force_bytes(user.last_name), res[0][1]["sn"])
