"""
Misc. utilities.
"""
from modoboa.lib.webutils import NavigationParameters


def decode_payload(encoding, payload):
    """Decode the payload according to the given encoding

    Supported encodings: base64, quoted-printable.

    :param encoding: the encoding's name
    :param payload: the value to decode
    :return: a string
    """
    encoding = encoding.lower()
    if encoding == "base64":
        import base64
        return base64.b64decode(payload)
    elif encoding == "quoted-printable":
        import quopri
        return quopri.decodestring(payload)
    return payload


class WebmailNavigationParameters(NavigationParameters):
    """
    Specific NavigationParameters subclass for the webmail.
    """
    def __init__(self, request, defmailbox=None):
        super(WebmailNavigationParameters, self).__init__(
            request, 'webmail_navparams'
        )
        if defmailbox is not None:
            self.parameters += [('mbox', defmailbox, False)]
