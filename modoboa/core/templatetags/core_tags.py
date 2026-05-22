"""Custom tags for Core application."""

import os

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def get_modoboa_logo(context):
    """Return the auth-page logo.

    Resolution order: theme parameter (populated by the ``theme`` context
    processor, so plugin signal overrides apply) > ``MODOBOA_CUSTOM_LOGO``
    Django setting > bundled static asset.
    """
    url = context.get("theme_login_logo_url")
    if url:
        return url
    try:
        logo = settings.MODOBOA_CUSTOM_LOGO
    except AttributeError:
        logo = None
    if logo is None:
        return os.path.join(settings.STATIC_URL, "css/modoboa-white.png")
    return logo
