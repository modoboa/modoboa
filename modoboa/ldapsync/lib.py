"""LDAP related functions."""

from __future__ import unicode_literals

import base64

import ldap
import ldap.modlist as modlist

from django.utils.encoding import force_bytes, force_str
from django.utils import six
from django.utils.translation import ugettext as _

from modoboa.lib.exceptions import InternalError


def get_connection(config):
    """Get a new connection to the LDAP directory."""
    uri = "{}:{}".format(
        config["ldap_server_address"], config["ldap_server_port"])
    uri = "{}://{}".format(
        "ldaps" if config["ldap_secured"] == "ssl" else "ldap", uri)
    conn = ldap.initialize(uri, bytes_mode=six.PY2)
    conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
    conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
    conn.simple_bind_s(
        force_str(config["ldap_sync_bind_dn"]),
        force_str(config["ldap_sync_bind_password"])
    )
    return conn


def create_ldap_account(user, dn, conn):
    """Create new account."""
    attrs = {
        "objectClass": [
            force_bytes("inetOrgPerson"), force_bytes("organizationalPerson")
        ],
        "uid": [force_bytes(user.username)],
        "sn": [force_bytes(user.last_name)],
        "givenName": [force_bytes(user.first_name)],
        "cn": [force_bytes(user.username)],
        "displayName": [force_bytes(user.fullname)],
        "mail": [force_bytes(user.email), force_bytes(user.secondary_email)],
        "homePhone": [force_bytes(user.phone_number)],
        "userPassword": base64.b64encode(force_bytes(user.password))
    }
    ldif = modlist.addModlist(attrs)
    try:
        conn.add_s(dn, ldif)
    except ldap.LDAPError as e:
        raise InternalError(
            _("Failed to create LDAP account: {}").format(e)
        )


def check_if_dn_exists(conn, dn):
    """Check if DN already exists in directory."""
    try:
        res = conn.search_s(
            force_str(dn), ldap.SCOPE_SUBTREE,
            force_str("(&(objectClass=inetOrgPerson))")
        )
        res = res[0][0]
    except ldap.LDAPError:
        return False
    return True


def update_ldap_account(user, config):
    """Update existing account."""
    dn = config["ldap_sync_account_dn_template"] % {"user": user.username}
    conn = get_connection(config)
    if not check_if_dn_exists(conn, dn):
        create_ldap_account(user, dn, conn)
        return
    password = user.password
    if not user.is_active:
        password = "#{}".format(user.password)
    ldif = [
        (ldap.MOD_REPLACE, "uid", force_bytes(user.username)),
        (ldap.MOD_REPLACE, "sn", force_bytes(user.last_name)),
        (ldap.MOD_REPLACE, "givenName", force_bytes(user.first_name)),
        (ldap.MOD_REPLACE, "cn", force_bytes(user.username)),
        (ldap.MOD_REPLACE, "displayName", force_bytes(user.fullname)),
        (ldap.MOD_REPLACE, "mail", force_bytes(user.email)),
        (ldap.MOD_REPLACE, "homePhone", force_bytes(user.phone_number)),
        (ldap.MOD_REPLACE, "userPassword",
         base64.b64encode(force_bytes(password))),
    ]
    try:
        conn.modify_s(dn, ldif)
    except ldap.LDAPError as e:
        raise InternalError(
            _("Failed to update account: {}").format(e))
