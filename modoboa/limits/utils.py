"""Modoboa limits utilities."""

from . import constants


def get_user_limit_templates():
    """Return defined templates."""
    return list(constants.DEFAULT_USER_LIMITS.items())


def get_domain_limit_templates():
    """Return defined templates."""
    return list(constants.DEFAULT_DOMAIN_LIMITS.items())


def move_pool_resource(owner, user):
    """Move resource from one pool to another.

    When an account doesn't need a pool anymore, we move the
    associated resource to the pool of its owner.
    """
    for name, _definition in get_user_limit_templates():
        user_limit = user.userobjectlimit_set.get(name=name)
        if user_limit.max_value < 0:
            continue
        owner_limit = owner.userobjectlimit_set.get(name=name)
        owner_limit.max_value += user_limit.max_value
        owner_limit.save()
