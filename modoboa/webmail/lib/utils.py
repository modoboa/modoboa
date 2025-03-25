"""Misc. utilities."""


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
