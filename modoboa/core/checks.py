from django.core.checks import register, Info, Warning
from django.conf import settings
from django.utils.translation import gettext as _

from modoboa.core.utils import generate_rsa_private_key


W001 = Warning(
    _(
        "You have USE_TZ set to False, this may result in issues during "
        "transitions between summer/winter time (ie the same local time occuring "
        "twice due to clock change)."
    ),
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


@register(deploy=True)
def check_rsa_private_key_exists(app_configs, **kwargs):
    """
    Ensure an RSA private key exists to enable OIDC.
    """
    msgs = []
    if generate_rsa_private_key(settings.BASE_DIR):
        msgs.append(Info("An RSA private key has been generated for OIDC."))
    return msgs
