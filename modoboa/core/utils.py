"""Utility functions."""

from django.contrib.sites.models import get_current_site

from modoboa.lib import parameters
from modoboa.lib.api_client import ModoAPIClient


def new_version_available(request):
    """Check if a new version of Modoboa is available."""
    if parameters.get_admin("CHECK_NEW_VERSIONS") == "no":
        return None
    return ModoAPIClient().current_version(get_current_site(request))
