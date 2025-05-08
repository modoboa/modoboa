"""Misc. utilities."""

import lxml


def html2plaintext(content: str) -> str:
    """HTML to plain text translation.

    :param content: some HTML content
    """
    if not content:
        return ""
    html = lxml.html.fromstring(content)
    plaintext = ""
    for ch in html.iter():
        p = None
        if ch.text is not None:
            p = ch.text.strip("\r\t\n")
        if ch.tag == "img":
            p = ch.get("alt")
        if p is None:
            continue
        plaintext += p + "\n"
    return plaintext


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
