"""Modoboa core template context processors."""

from modoboa.parameters import tools as param_tools


def theme(request):
    """Expose theme colors to all templates.

    ``registration/base.html`` references these on every auth-related
    page, including Django's built-in views (e.g.
    ``PasswordResetConfirmView``), which would otherwise render with
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
