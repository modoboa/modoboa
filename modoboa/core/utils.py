# -*- coding: utf-8 -*-

"""Utility functions."""

from __future__ import unicode_literals

from pkg_resources import parse_version

from django.utils.translation import ugettext as _

from modoboa.core.extensions import exts_pool
from modoboa.lib.api_client import ModoAPIClient
from . import models


def parse_map_file(path):
    """Parse a postfix map file and return values."""
    content = {}
    with open(path) as fp:
        for line in fp:
            if not line or line.startswith("#"):
                continue
            name, value = line.split("=", 1)
            content[name.strip()] = value.strip()
    return content


def check_for_updates(request):
    """Check if a new version of Modoboa is available."""
    local_config = models.LocalConfig.objects.first()
    client = ModoAPIClient()
    extensions = exts_pool.list_all()
    extensions = [{
        "label": "Modoboa",
        "name": "modoboa",
        "description": _("The core part of Modoboa"),
        "version": client.local_core_version
    }] + extensions
    update_avail = False
    for extension in extensions:
        pkgname = extension["name"].replace("_", "-")
        for api_extension in local_config.api_versions:
            if api_extension["name"] != pkgname:
                continue
            extension["last_version"] = api_extension["version"]
            if (
                parse_version(api_extension["version"]) >
                parse_version(extension["version"])
            ):
                extension["update"] = True
                extension["changelog_url"] = api_extension["url"]
                update_avail = True
                break
    return update_avail, extensions
