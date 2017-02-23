"""Admin models."""

from .base import AdminObject
from .domain import Domain, MXRecord, DNSBLResult
from .domain_alias import DomainAlias
from .mailbox import Mailbox, Quota, MailboxOperation, SenderAddress
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
