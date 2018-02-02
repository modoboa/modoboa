# -*- coding: utf-8 -*-

"""A client for Modoboa's public API."""

from __future__ import unicode_literals

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

    def list_extensions(self):
        """List all official extensions."""
        url = os.path.join(self._api_url, "extensions/")
        return self.__send_request(url)

    def register_instance(self, hostname):
        """Register this instance."""
        url = "{}instances/search/?hostname={}".format(
            self._api_url, hostname)
        instance = self.__send_request(url)
        if instance is None:
            url = "{}instances/".format(self._api_url)
            data = {
                "hostname": hostname, "known_version": self.local_core_version}
            response = requests.post(url, data=data)
            if response.status_code != 201:
                return None
            instance = response.json()
        return int(instance["pk"])

    def update_instance(self, pk, data):
        """Update instance and send stats."""
        url = "{}instances/{}/".format(self._api_url, pk)
        response = requests.put(url, data=data)
        response.raise_for_status()

    def versions(self):
        """Fetch core and extension versions."""
        url = "{}versions/".format(self._api_url)
        return self.__send_request(url)
