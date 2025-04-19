"""Webmail constants."""

from enum import Enum

from django.utils.translation import gettext_lazy as _


MAILBOX_TYPES = ["inbox", "draft", "sent", "junk", "trash", "normal"]


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
