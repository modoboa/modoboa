"""Deployment checks."""

from django.core.checks import Warning, register

from django.utils.translation import gettext as _

from modoboa.core import models as core_models


W001 = Warning(
    _(
        "Automatic domain/mailbox creation is disabled which means IMAP "
        "authentication won't work."
    ),
    hint=_(
        "Go to the online parameters panel (admin tab) and activate " "this feature."
    ),
    id="modoboa-imap-migration.W001",
)


@register(deploy=True)
def check_auto_creation_is_enabled(app_configs, **kwargs):
    """Ensure automatic domain/mailbox creation is on."""
    lc = core_models.LocalConfig.objects.first()
    if not lc:
        return []
    errors = []
    if not lc.parameters.get_value("auto_create_domain_and_mailbox", app="admin"):
        errors.append(W001)
    return errors
