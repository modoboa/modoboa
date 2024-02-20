"""PDF credentials constants."""

from django.utils.translation import gettext_lazy


CONNECTION_SECURITY_MODES = [
    ("none", gettext_lazy("None")),
    ("starttls", "STARTTLS"),
    ("tls", "TLS"),
]
