"""Admin models."""

from .alarm import Alarm
from .alias import Alias, AliasRecipient, validate_alias_address
from .base import AdminObject
from .domain import Domain
from .domain_alias import DomainAlias
from .mailbox import (
    AnyoneShare,
    Mailbox,
    MailboxOperation,
    Quota,
    SenderAddress,
    UserShare,
)
from .mxrecord import DNSBLResult, MXRecord

__all__ = [
    "Alarm",
    "AdminObject",
    "Alias",
    "AliasRecipient",
    "AnyoneShare",
    "DNSBLResult",
    "Domain",
    "DomainAlias",
    "Mailbox",
    "MailboxOperation",
    "MXRecord",
    "Quota",
    "SenderAddress",
    "UserShare",
    "validate_alias_address",
]
