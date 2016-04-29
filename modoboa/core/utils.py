"""Utility functions."""

from django.utils.translation import ugettext as _

from django.contrib.sites.shortcuts import get_current_site

from modoboa.core.extensions import exts_pool
from modoboa.lib import parameters
from modoboa.lib.api_client import ModoAPIClient


def check_for_updates(request):
    """Check if a new version of Modoboa is available."""
    if parameters.get_admin("CHECK_NEW_VERSIONS") == "no":
        return False, []
    client = ModoAPIClient()
    extensions = exts_pool.list_all(True)
    extensions = [{
        "label": "Modoboa",
        "description": _("The core part of Modoboa"),
        "update": client.new_core_version(get_current_site(request)),
        "last_version": client.latest_core_version,
        "changelog_url": client.changelog_url,
        "version": client.local_core_version
    }] + extensions
    update_avail = False
    for extension in extensions:
        if extension.get("update"):
            update_avail = True
            break
    return update_avail, extensions
