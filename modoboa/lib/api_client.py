"""A client for Modoboa's public API."""

import os
import pkg_resources

import requests
from requests.exceptions import RequestException

from django.conf import settings

from versionfield.constants import DEFAULT_NUMBER_BITS
from versionfield.version import Version


class ModoAPIClient(object):

    """A simple client for the public API."""

    def __init__(self, api_url=None):
        """Constructor."""
        self._api_url = (
            settings.MODOBOA_API_URL if api_url is None
            else api_url
        )

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

    def current_version(self, site):
        """Check the latest version."""
        client_version = pkg_resources.get_distribution("modoboa").version
        url = os.path.join(self._api_url, "current_version/")
        params = {"client_version": client_version, "site": site}
        resp = self.__send_request(url, params)
        if resp is None:
            return None
        version = Version(resp["version"], DEFAULT_NUMBER_BITS)
        if version <= Version(client_version, DEFAULT_NUMBER_BITS):
            return None
        return resp

    def list_extensions(self):
        """List all official extensions."""
        url = os.path.join(self._api_url, "extensions/")
        return self.__send_request(url)
