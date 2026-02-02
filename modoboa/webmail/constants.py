"""Webmail constants."""

from enum import Enum

from django.utils.translation import gettext_lazy as _


MAILBOX_TYPES = ["inbox", "draft", "sent", "scheduled", "junk", "trash", "normal"]

MAILBOX_NAME_SCHEDULED = "Scheduled"

CUSTOM_HEADER_SCHEDULED_ID = "X-Scheduled-ID"
CUSTOM_HEADER_SCHEDULED_DATETIME = "X-Scheduled-Datetime"


class SchedulingState(Enum):
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SEND_ERROR = "send_error"
    MOVE_ERROR = "move_error"


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
