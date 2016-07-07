"""Shortcuts."""

from .alias import AliasDetailView
from .identity import AccountDetailView
from .dnsbl import DNSBLDomainDetailView
from .domain import DomainDetailView


__all__ = [
    "AccountDetailView",
    "AliasDetailView",
    "DNSBLDomainDetailView",
    "DomainDetailView",
]
