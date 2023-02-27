"""PDF credentials constants."""

from django.utils.translation import ugettext_lazy


CONNECTION_SECURITY_MODES = [
    ("none", ugettext_lazy("None")),
    ("starttls", "STARTTLS"),
    ("tls", "TLS")
]
