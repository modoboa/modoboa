# coding: utf-8
"""
:mod:`controls` --- provides event handlers that check if limits are reached
----------------------------------------------------------------------------

"""

from modoboa.lib import events, parameters
from modoboa.lib.permissions import get_object_owner

from . import utils


def move_pool_resource(owner, user):
    """Move resource from one pool to another

    When an account doesn't need a pool anymore, we move the
    associated resource to the pool of its owner.
    """
    if not owner.is_superuser:
        for name, ltpl in utils.get_user_limit_templates():
            l = user.userobjectlimit_set.get(name=name)
            if l.max_value < 0:
                continue
            ol = owner.userobjectlimit_set.get(name=name)
            ol.max_value += l.max_value
            ol.save()


@events.observe("UserCanSetRole")
def user_can_set_role(user, role, account=None):
    """Check if the user can still set this role.

    The only interesting case concerns resellers defining new domain
    administrators. We want to check if they are allowed to do this
    operation before any modification is made to :keyword:`account`.

    :param ``User`` user: connected user
    :param ``User`` account: account modified (None on creation)
    :param str newrole: role to check
    """
    condition = (
        parameters.get_admin("ENABLE_ADMIN_LIMITS") == "no" or
        role != "DomainAdmins")
    if condition:
        return [True]
    lname = "domain_admins"
    condition = (
        user.is_superuser or
        not user.userobjectlimit_set.get(name=lname).is_exceeded()
    )
    if condition:
        return [True]
    if account is not None and account.role == role:
        return [True]
    return [False]


@events.observe("AccountModified")
def on_account_modified(old, new):
    """Update limits when roles are updated"""
    owner = get_object_owner(old)
    if owner.role not in ["SuperAdmins", "Resellers"]:
        # Domain admins can't change the role so nothing to check.
        return

    if new.role not in ["DomainAdmins", "Resellers"]:
        move_pool_resource(owner, new)


@events.observe("AccountDeleted")
def on_account_deleted(account, byuser, **kwargs):
    owner = get_object_owner(account)
    if owner.role not in ["SuperAdmins", "Resellers"]:
        return

    move_pool_resource(owner, account)
