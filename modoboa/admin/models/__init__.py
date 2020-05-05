"""Admin models."""

from .alias import Alias, AliasRecipient
from .base import AdminObject
from .domain import Domain
from .domain_alias import DomainAlias
from .mailbox import Mailbox, MailboxOperation, Quota, SenderAddress
from .mxrecord import DNSBLResult, MXRecord

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
