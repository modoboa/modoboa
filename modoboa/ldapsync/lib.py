"""LDAP related functions."""

import ldap
import ldap.modlist as modlist

from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from django.utils.translation import ugettext as _

from modoboa.core import models as core_models
from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.exceptions import InternalError


def create_connection(srv_address, srv_port, config, username, password):
    """Create a new connection with given server."""
    uri = "{}:{}".format(srv_address, srv_port)
    uri = "{}://{}".format(
        "ldaps" if config["ldap_secured"] == "ssl" else "ldap", uri)
    conn = ldap.initialize(uri)
    conn.protocol_version = 3
    conn.set_option(ldap.OPT_X_TLS_DEMAND, True)
    conn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
    conn.set_option(ldap.OPT_REFERRALS, 0)
    conn.simple_bind_s(
        force_str(username if username else config["ldap_sync_bind_dn"]),
        force_str(password if password else config["ldap_sync_bind_password"])
    )
    return conn


def get_connection(config, username=None, password=None):
    """Get a new connection to the LDAP directory."""
    try:
        conn = create_connection(
            config["ldap_server_address"], config["ldap_server_port"],
            config, username, password
        )
    except ldap.LDAPError:
        if not config["ldap_enable_secondary_server"]:
            raise
        conn = create_connection(
            config["ldap_secondary_server_address"],
            config["ldap_secondary_server_port"],
            config, username, password
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


def find_user_groups(conn, config, dn, entry):
    """Retrieve groups for given user."""
    condition = (
        config["ldap_is_active_directory"] or
        config["ldap_group_type"] == "groupofnames"
    )
    if condition:
        flt = "(member={})"
    elif config["ldap_group_type"] == "posixgroup":
        flt = "(memberUid={})"

    result = conn.search_s(
        config["ldap_groups_search_base"],
        ldap.SCOPE_SUBTREE,
        flt.format(dn)
    )
    groups = []
    for dn, entry in result:
        if not dn:
            continue
        if "," in groups:
            groups.append(dn.split(',')[0].split('=')[1])
        else:
            groups.append(dn)
    return groups


def user_is_disabled(config, entry):
    """Check if LDAP user is disabled or not."""
    if config["ldap_is_active_directory"]:
        if "userAccountControl" in entry:
            value = int(force_str(entry["userAccountControl"][0]))
            return value == 514
    # FIXME: is there a way to detect a disabled user with OpenLDAP?
    return False


def import_accounts_from_ldap(config):
    """Import user accounts from LDAP directory."""
    conn = get_connection(config)
    result = conn.search_s(
        config["ldap_import_search_base"],
        ldap.SCOPE_SUBTREE,
        config["ldap_import_search_filter"]
    )
    admin_groups = config["ldap_admin_groups"].split(";")
    for dn, entry in result:
        role = "SimpleUsers"
        groups = find_user_groups(conn, config, dn, entry)
        for grp in admin_groups:
            if grp.strip() in groups:
                role = "DomainAdmins"
                break
        username = force_str(entry[config["ldap_import_username_attr"]][0])
        if role == "SimpleUsers":
            lpart, domain = split_mailbox(username)
            if domain is None:
                # Try to find associated email
                username = None
                for attr in ["mail", "userPrincipalName"]:
                    if attr in entry:
                        username = force_str(entry[attr][0])
                        break
                if username is None:
                    print("Skipping {} because no email found".format(dn))
                    continue
        defaults = {
            "username": username.lower(),
            "is_local": False,
            "language": settings.LANGUAGE_CODE
        }
        user, created = core_models.User.objects.get_or_create(
            username__iexact=username,
            defaults=defaults
        )
        if created:
            core_models.populate_callback(user, role)

        attr_map = {
            "first_name": "givenName",
            "email": "mail",
            "last_name": "sn"
        }
        for attr, ldap_attr in attr_map.items():
            if ldap_attr in entry:
                setattr(user, attr, force_str(entry[ldap_attr][0]))
            user.is_active = not user_is_disabled(config, entry)
            user.save()

        # FIXME: handle delete and rename operations?
