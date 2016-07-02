"""Modoboa limits utilities."""

from . import constants


def get_user_limit_templates():
    """Return defined templates."""
    # FIXME: change GetExtraLimitTemplates
    return constants.DEFAULT_USER_LIMITS.items()


def get_domain_limit_templates():
    """Return defined templates."""
    return constants.DEFAULT_DOMAIN_LIMITS.items()
