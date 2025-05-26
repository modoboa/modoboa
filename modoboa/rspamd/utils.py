"""Utilies for modoboa.rspamd plugin."""

import shutil

from django.core.exceptions import AppRegistryNotReady


def check_rspamd_installed():
    return shutil.which("rspamd") is not None


def get_rspamd_options():
    try:
        from modoboa.core import models

        is_rspamd_installed = check_rspamd_installed()
        if not is_rspamd_installed:
            return None
        rspamd_options = {}
        localconfig = models.LocalConfig.objects.first()
        rspamd_location = localconfig.parameters.get_value(
            "rspamd_dashboard_location", raise_exception=False
        )
        if not rspamd_location:
            return None
        rspamd_options["location"] = rspamd_location
        return rspamd_options
    except AppRegistryNotReady:
        # If the instance is not restarted after rspamd installation
        return None
