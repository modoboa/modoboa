"""Webmail constants."""

from datetime import timedelta
from enum import Enum

from django.utils.translation import gettext_lazy as _

MAILBOX_TYPES = [
    "inbox",
    "draft",
    "sent",
    "scheduled",
    "junk",
    "trash",
    "normal",
    "shared",
]

MAILBOX_NAME_SCHEDULED = "Scheduled"

# User parameters holding the name of a folder the webmail relies on
SPECIAL_MAILBOX_PARAMETERS = (
    "drafts_folder",
    "sent_folder",
    "junk_folder",
    "trash_folder",
)

# Rights (RFC 4314) given by each folder sharing level. Never "a": the
# recipient could share the folder again, with anyone.
SHARING_LEVELS = {
    "read": "lrs",
    "write": "lrswipte",
    "manage": "lrswipktex",
}
# Rights set by another client, matching no level
SHARING_LEVEL_CUSTOM = "custom"


def get_sharing_level(rights: str) -> str:
    """Return the sharing level matching the given rights."""
    # Servers add the obsolete c and d rights (RFC 4314, section 2.1.1)
    current = set(rights) - set("cd")
    for level, letters in SHARING_LEVELS.items():
        if set(letters) == current:
            return level
    return SHARING_LEVEL_CUSTOM


CUSTOM_HEADER_SCHEDULED_ID = "X-Scheduled-ID"
CUSTOM_HEADER_SCHEDULED_DATETIME = "X-Scheduled-Datetime"

# Inline images embedded as data: URIs when displaying a message
# (SVG is excluded on purpose: it can carry active content).
INLINE_IMAGE_MIME_TYPES = (
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
)


class SchedulingState(Enum):
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SEND_ERROR = "send_error"
    MOVE_ERROR = "move_error"


# A scheduled message still in the SENDING state after this delay is
# considered lost by the queue and flagged as failed.
SCHEDULED_SENDING_TIMEOUT = timedelta(hours=1)

EMAIL_SCHEDULING_STATES = (
    (SchedulingState.SCHEDULED.value, "scheduled"),
    (SchedulingState.SENDING.value, "sending"),
    (SchedulingState.SEND_ERROR.value, "send_error"),
    (SchedulingState.MOVE_ERROR.value, "move_error"),
)


class SmtpConnectionMode(Enum):
    NONE = "none"
    STARTTLS = "starttls"
    TLS = "ssl"


SMTP_CONNECTION_MODES = [
    (SmtpConnectionMode.NONE.value, _("None")),
    (SmtpConnectionMode.STARTTLS.value, "STARTTLS"),
    (SmtpConnectionMode.TLS.value, "SSL/TLS"),
]


class DisplayMode(Enum):
    PLAIN = "plain"
    HTML = "html"


DISPLAY_MODES = [
    (DisplayMode.PLAIN.value, "text"),
    (DisplayMode.HTML.value, "html"),
]


class SignaturePosition(Enum):
    ABOVE = "above"
    BELOW = "below"


SIGNATURE_POSITIONS = [
    (SignaturePosition.ABOVE.value, _("Above the quoted message")),
    (SignaturePosition.BELOW.value, _("Below the quoted message")),
]


class ListingMode(Enum):
    FLAT = "flat"
    THREADED = "threaded"


LISTING_MODES = [
    (ListingMode.FLAT.value, _("Messages")),
    (ListingMode.THREADED.value, _("Conversations")),
]
