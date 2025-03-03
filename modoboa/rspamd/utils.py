"""Utilies for modoboa.rspamd plugin."""

import shutil

from django.core.exceptions import AppRegistryNotReady

from modoboa.lib import signals as lib_signals


def check_rspamd_installed():
    try:
        is_rspamd_installed = shutil.which("rspamd") is not None
        rspamd_options = {} if is_rspamd_installed else None
        request = lib_signals.get_request()
        if is_rspamd_installed:
            if request is not None:
                rspamd_options["location"] = request.localconfig.parameters.get_value(
                    "rspamd_dashboard_location"
                )
            else:
                rspamd_options["location"] = None
    except AppRegistryNotReady:
        return None
    return rspamd_options
