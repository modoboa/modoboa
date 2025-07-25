from django.db.utils import ProgrammingError, OperationalError
from django.core.checks import register, Info, Warning, Error
from django.conf import settings
from django.utils.translation import gettext as _

from oauth2_provider.models import get_application_model

from modoboa.core.utils import (
    check_for_deprecated_password_schemes,
    generate_rsa_private_key,
)

W001 = Warning(
    _(
        "You have USE_TZ set to False, this may result in issues during "
        "transitions between summer/winter time (ie the same local time occuring "
        "twice due to clock change)."
    ),
    hint=_("Set `USE_TZ = True` in settings.py"),
    id="modoboa.core.W001",
)
W002 = Warning(
    _("The password scheme you are using is deprecated."),
    hint=_("Upgrade your password scheme to a stronger one"),
    id="modoboa.core.W002",
)

E001 = Error(
    _(
        "Oauth2 application for dovecot has not been found."
        " Webmail and some other features won't be available."
    ),
    hint=_(
        "Visit : https://modoboa.readthedocs.io/en/latest/manual_installation/dovecot.html#dovecot-oauth2"
    ),
    id="modoboa.core.E001",
)

E002 = Error(
    _(
        "Oauth2 application for radicale has not been found."
        " Calendar and some other features won't be available."
    ),
    hint=_(
        "Visit :  https://modoboa.readthedocs.io/en/latest/manual_installation/radicale.html#radicale-oauth2"
    ),
    id="modoboa.core.E002",
)


def oauth_app_exists(app_name):
    oauth_application = get_application_model().objects.filter(name=app_name)
    return oauth_application.exists()


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


@register()
def check_password_hasher(app_configs, **kwargs):
    msgs = []
    try:
        hasher = check_for_deprecated_password_schemes()
    except (ProgrammingError, OperationalError):
        # This is probably a fresh install...
        return []
    if hasher:
        msgs.append(W002)
    return msgs


@register(deploy=True)
def check_dovecot_oauth_app(*args, **kwargs):
    error = []
    if not oauth_app_exists("Dovecot"):
        error.append(E001)
    return error


@register(deploy=True)
def check_radicale_oauth_app(*args, **kwargs):
    error = []
    if not oauth_app_exists("Radicale"):
        error.append(E002)
    return error
