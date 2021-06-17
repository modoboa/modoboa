"""Shortcuts."""

from .alias import AliasDetailView
from .dns import DNSBLDomainDetailView, MXDomainDetailView
from .domain import DomainAlarmsView, DomainDetailView
from .identity import AccountDetailView

__all__ = [
    "AccountDetailView",
    "AliasDetailView",
    "DNSBLDomainDetailView",
    "DomainAlarmsView",
    "DomainDetailView",
    "MXDomainDetailView",
]
