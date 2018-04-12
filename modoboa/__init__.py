# -*- coding: utf-8 -*-

"""Modoboa - Mail hosting made simple."""

from __future__ import unicode_literals

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
