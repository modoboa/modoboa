"""Webmail constants."""

from datetime import timedelta
from enum import Enum

from django.utils.translation import gettext_lazy as _

MAILBOX_TYPES = ["inbox", "draft", "sent", "scheduled", "junk", "trash", "normal"]

MAILBOX_NAME_SCHEDULED = "Scheduled"

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
