# -*- coding: utf-8 -*-

"""Shortcuts."""

from __future__ import unicode_literals

from .alias import AliasDetailView
from .dns import DNSBLDomainDetailView, MXDomainDetailView
from .domain import DomainDetailView
from .identity import AccountDetailView

__all__ = [
    "AccountDetailView",
    "AliasDetailView",
    "DNSBLDomainDetailView",
    "DomainDetailView",
    "MXDomainDetailView",
]
