"""Modoboa limits utilities."""

from . import constants


def get_user_limit_templates():
    """Return defined templates."""
    return constants.DEFAULT_USER_LIMITS.items()


def get_domain_limit_templates():
    """Return defined templates."""
    return constants.DEFAULT_DOMAIN_LIMITS.items()


def move_pool_resource(owner, user):
    """Move resource from one pool to another.

    When an account doesn't need a pool anymore, we move the
    associated resource to the pool of its owner.
    """
    for name, ltpl in get_user_limit_templates():
        l = user.userobjectlimit_set.get(name=name)
        if l.max_value < 0:
            continue
        ol = owner.userobjectlimit_set.get(name=name)
        ol.max_value += l.max_value
        ol.save()
