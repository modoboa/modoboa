"""Modoboa core template context processors."""

from modoboa.parameters import tools as param_tools


def theme(request):
    """Expose theme colors to all templates.

    Modoboa's own views inject these via ``ModoboaThemeMixin``, but
    Django's built-in auth views (e.g. ``PasswordResetConfirmView``)
    don't — so ``registration/base.html`` would otherwise render with
    empty color values.
    """
    try:
        params = dict(param_tools.get_global_parameters(app="core"))
    except Exception:
        return {}
    return {
        "theme_primary_color": params.get("theme_primary_color", ""),
        "theme_primary_color_dark": params.get("theme_primary_color_dark", ""),
    }
