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

    # "-- " lets clients recognize (and hide) signatures (RFC 3676)

    def _format_sig_plain(self, content):
        self._sig = f"-- \n{html2plaintext(content)}"

    def _format_sig_html(self, content):
        self._sig = f"<p>-- </p>{content}"

    def __str__(self):
        return self._sig
