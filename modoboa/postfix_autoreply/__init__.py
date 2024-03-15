# -*- coding: utf-8 -*-

"""Away message editor for Modoboa (postfix compatible)."""

from __future__ import unicode_literals

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

default_app_config = "modoboa_postfix_autoreply.apps.PostfixAutoreplyConfig"
