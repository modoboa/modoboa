"""Admin models."""

from __future__ import unicode_literals

from .base import AdminObject
from .domain import Domain
from .domain_alias import DomainAlias
from .mailbox import Mailbox, Quota, MailboxOperation, SenderAddress
from .mxrecord import DNSBLResult, MXRecord
from .alias import Alias, AliasRecipient

__all__ = [
    "AdminObject",
    "Alias",
    "AliasRecipient",
    "DNSBLResult",
    "Domain",
    "DomainAlias",
    "Mailbox",
    "MailboxOperation",
    "MXRecord",
    "Quota",
    "SenderAddress",
]
