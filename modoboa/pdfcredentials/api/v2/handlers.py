"""Handlers for PDF credientials api v2."""

import os

from django.urls import reverse
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from modoboa.admin import signals as admin_signals
from modoboa.parameters import tools as param_tools

from ...lib import get_creds_filename


@receiver(admin_signals.extra_account_identities_actions)
def extra_identities_actions(sender, account, **kwargs):
    """
    Add download credential action for identity.
    Used for api v2.
    """
    if not param_tools.get_global_parameter("enabled_pdfcredentials"):
        return []
    fname = get_creds_filename(account)
    if not os.path.exists(fname):
        return []
    return {
        "name": "get_credentials",
        "url":  reverse("v2:get-credentials",
                       args=[account.id]),
        "icon": "mdi-file-download-outline",
        "label": _("Download PDF credentials.")
    }
