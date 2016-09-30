"""Shortcuts."""

from .alias import AliasDetailView
from .identity import AccountDetailView
from .dns import DNSBLDomainDetailView, MXDomainDetailView
from .domain import DomainDetailView, DomainStatisticsView


__all__ = [
    "AccountDetailView",
    "AliasDetailView",
    "DNSBLDomainDetailView",
    "DomainDetailView",
    "DomainStatisticsView",
    "MXDomainDetailView",
]
