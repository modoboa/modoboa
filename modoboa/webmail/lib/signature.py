"""Tools to deal with message signatures."""

from modoboa.webmail.lib.utils import html2plaintext


class EmailSignature:
    """User signature.

    :param user: User object
    """

    def __init__(self, user):
        self._sig = ""
        dformat = user.parameters.get_value("editor")
        content = user.parameters.get_value("signature")
        if content and len(content):
            getattr(self, f"_format_sig_{dformat}")(content)

    def _format_sig_plain(self, content):
        self._sig = f"""
---
{html2plaintext(content)}"""

    def _format_sig_html(self, content):
        content = f"---<br>{content}"
        self._sig = content
        return

    def __str__(self):
        return self._sig
