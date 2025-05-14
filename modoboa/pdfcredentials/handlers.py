"""PDF credentials handlers."""

import logging

from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import gettext as _

from modoboa.core import models as core_models
from modoboa.core import signals as core_signals
from modoboa.lib.exceptions import InternalError
from modoboa.parameters import tools as param_tools

from .documents import credentials
from .lib import init_storage_dir, delete_credentials


@receiver(core_signals.account_password_updated)
def password_updated(sender, account, password, created, **kwargs):
    """Create or update document."""
    if not param_tools.get_global_parameter("enabled_pdfcredentials"):
        return
    generate_at_creation = param_tools.get_global_parameter("generate_at_creation")
    if (generate_at_creation and not created) or account.is_superuser:
        return
    try:
        init_storage_dir()
    except InternalError:
        logger = logging.getLogger("modoboa.admin")
        logger.error(
            _(
                "Failed to create PDF_credentials directory. "
                "Please check the permissions or the path."
            )
        )
    credentials(account, password)


@receiver(signals.pre_delete, sender=core_models.User)
def account_deleted(sender, instance, **kwargs):
    """Remove document."""
    delete_credentials(instance)
