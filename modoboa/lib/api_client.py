"""A client for Modoboa's public API."""

import os
import pkg_resources

import requests
from requests.exceptions import RequestException


class ModoAPIClient(object):

    """A simple client for the public API."""

    def __init__(self, api_url=None):
        """Constructor."""
        if api_url is None:
            from django.conf import settings
            self._api_url = settings.MODOBOA_API_URL
        else:
            self._api_url = api_url
        self._local_core_version = None
        self._latest_core_version = None
        self.changelog_url = None

    def __send_request(self, url, params=None):
        """Send a request to the API."""
        if params is None:
            params = {}
        try:
            resp = requests.get(url, params=params)
        except RequestException:
            return None
        if resp.status_code != 200:
            return None
        return resp.json()

    @property
    def local_core_version(self):
        """Return the version installed locally."""
        if self._local_core_version is None:
            self._local_core_version = pkg_resources.get_distribution(
                "modoboa").version
        return self._local_core_version

    @property
    def latest_core_version(self):
        """Return the latest core version."""
        if self._latest_core_version is None:
            return self._local_core_version
        return self._latest_core_version

    def new_core_version(self, site):
        """Check the latest version."""
        from versionfield.constants import DEFAULT_NUMBER_BITS
        from versionfield.version import Version

        url = os.path.join(self._api_url, "current_version/")
        params = {
            "client_version": self.local_core_version, "client_site": site
        }
        resp = self.__send_request(url, params)
        if resp is None:
            return None
        version = Version(resp["version"], DEFAULT_NUMBER_BITS)
        if version <= Version(self.local_core_version, DEFAULT_NUMBER_BITS):
            return False
        self._latest_core_version = resp["version"]
        self.changelog_url = resp["changelog_url"]
        return True

    def list_extensions(self):
        """List all official extensions."""
        url = os.path.join(self._api_url, "extensions/")
        return self.__send_request(url)
