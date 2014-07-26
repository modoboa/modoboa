"""
Utility functions.
"""
import os
import pkg_resources

import requests

from django.conf import settings

from versionfield.constants import DEFAULT_NUMBER_BITS
from versionfield.version import Version

from modoboa.lib import parameters


def new_version_available():
    """Check if a new version of Modoboa is available."""
    if parameters.get_admin("CHECK_NEW_VERSIONS") == "no":
        return None
    local_version = pkg_resources.get_distribution("modoboa").version
    url = os.path.join(settings.MODOBOA_API_URL, "current_version/")
    resp = requests.get(url, params={
        "client_version": pkg_resources.get_distribution("modoboa").version
    })
    if resp.status_code != 200:
        return None
    resp = resp.json()
    version = Version(resp["version"], DEFAULT_NUMBER_BITS)
    if version <= Version(local_version, DEFAULT_NUMBER_BITS):
        return None
    return resp
