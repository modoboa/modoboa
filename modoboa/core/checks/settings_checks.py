from django.conf import settings
from django.core.checks import Warning, register
from django.utils.translation import ugettext as _

W001 = Warning(
    _("You have USE_TZ set to False, this may result in issues during "
      "transitions between summer/winter time (ie the same local time occuring "
      "twice due to clock change)."),
    hint=_("Set `USE_TZ = True` in settings.py"),
    id="modoboa.W001",
)


@register(deploy=True)
def check_use_tz_enabled(app_configs, **kwargs):
    """Ensure USE_TZ is enabled in settings.py

    When USE_TZ is enabled all date/times are stored in UTC.
    Fixes #1086 - https://github.com/modoboa/modoboa/issues/1086
    """
    errors = []
    if not settings.USE_TZ:
        errors.append(W001)
    return errors
