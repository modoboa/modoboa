"""Shortcuts."""

from .alias import AliasDetailView
from .identity import AccountDetailView
from .dns import DNSBLDomainDetailView, MXDomainDetailView
from .domain import DomainDetailView


__all__ = [
    "AccountDetailView",
    "AliasDetailView",
    "DNSBLDomainDetailView",
    "DomainDetailView",
    "MXDomainDetailView",
]
