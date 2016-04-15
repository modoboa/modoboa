"""Modoboa limits utilities."""

from . import constants


def get_limit_templates():
    """Return defined templates."""
    # FIXME: change GetExtraLimitTemplates
    return constants.DEFAULT_LIMITS.items()
