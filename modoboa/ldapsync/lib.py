"""LDAP related functions."""

from __future__ import unicode_literals

import ldap
import ldap.modlist as modlist

from django.utils.encoding import force_bytes, force_str
from django.utils.translation import ugettext as _

from modoboa.lib.exceptions import InternalError


def get_connection(config, username=None, password=None):
    """Get a new connection to the LDAP directory."""
    uri = "{}:{}".format(
        config["ldap_server_address"], config["ldap_server_port"])
    uri = "{}://{}".format(
        "ldaps" if config["ldap_secured"] == "ssl" else "ldap", uri)
    conn = ldap.initialize(uri)
    conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
    conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
    conn.simple_bind_s(
        force_str(username if username else config["ldap_sync_bind_dn"]),
        force_str(password if password else config["ldap_sync_bind_password"])
    )
    return conn


def get_user_password(user, disable=False):
    """Return ready-to-use password from user instance."""
    scheme, password = user.password.split("}")
    return (
        force_bytes(scheme) +
        b"}" +
        b"#" if disable else b"" +
        force_bytes(password)
    )


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
        "mail": [
            force_bytes(user.email), force_bytes(user.secondary_email)],
        "homePhone": [force_bytes(user.phone_number)],
    }
    if user.password:
        scheme, password = user.password.split("}")
        attrs["userPassword"] = [get_user_password(user)]
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
    ldif = [
        (ldap.MOD_REPLACE, "uid", force_bytes(user.username)),
        (ldap.MOD_REPLACE, "sn", force_bytes(user.last_name)),
        (ldap.MOD_REPLACE, "givenName", force_bytes(user.first_name)),
        (ldap.MOD_REPLACE, "cn", force_bytes(user.username)),
        (ldap.MOD_REPLACE, "displayName", force_bytes(user.fullname)),
        (ldap.MOD_REPLACE, "mail", force_bytes(user.email)),
        (ldap.MOD_REPLACE, "homePhone", force_bytes(user.phone_number)),
    ]
    if user.password:
        password = get_user_password(user, not user.is_active)
        ldif.append((ldap.MOD_REPLACE, "userPassword", password))
    try:
        conn.modify_s(dn, ldif)
    except ldap.LDAPError as e:
        raise InternalError(
            _("Failed to update LDAP account: {}").format(e))


def delete_ldap_account(user, config):
    """Delete remote LDAP account."""
    dn = config["ldap_sync_account_dn_template"] % {"user": user.username}
    conn = get_connection(config)
    if not check_if_dn_exists(conn, dn):
        return
    if config["ldap_sync_delete_remote_account"]:
        try:
            conn.delete_s(dn)
        except ldap.LDAPError as e:
            raise InternalError(
                _("Failed to delete LDAP account: {}").format(e)
            )
    else:
        password = get_user_password(user, True)
        ldif = [
            (ldap.MOD_REPLACE, "userPassword", password)
        ]
        try:
            conn.modify_s(dn, ldif)
        except ldap.LDAPError as e:
            raise InternalError(
                _("Failed to disable LDAP account: {}").format(e))
