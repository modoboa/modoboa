"""
Copy of the original rfc6266 package, just the generation part.

Orginal code is available at https://github.com/g2p/rfc6266.
"""

from urllib.parse import quote


# RFC 2616
separator_chars = "()<>@,;:\\\"/[]?={} \t"
# RFC 5987
attr_chars_nonalnum = '!#$&+-.^_`|~'


def percent_encode(string, safe, encoding):
    return quote(string, safe, encoding, errors='strict')


def is_token_char(ch):
    # Must be ascii, and neither a control char nor a separator char
    asciicode = ord(ch)
    # < 128 means ascii, exclude control chars at 0-31 and 127,
    # exclude separator characters.
    return 31 < asciicode < 127 and ch not in separator_chars


def is_token(candidate):
    return all(is_token_char(ch) for ch in candidate)


def is_ascii(text):
    return all(ord(ch) < 128 for ch in text)


def fits_inside_codec(text, codec):
    try:
        text.encode(codec)
    except UnicodeEncodeError:
        return False
    else:
        return True


def is_lws_safe(text):
    return normalize_ws(text) == text


def normalize_ws(text):
    return ' '.join(text.split())


def qd_quote(text):
    return text.replace('\\', '\\\\').replace('"', '\\"')


def build_header(
    filename, disposition='attachment', filename_compat=None
):
    """Generate a Content-Disposition header for a given filename.
    For legacy clients that don't understand the filename* parameter,
    a filename_compat value may be given.
    It should either be ascii-only (recommended) or iso-8859-1 only.
    In the later case it should be a character string
    (unicode in Python 2).
    Options for generating filename_compat (only useful for legacy clients):
    - ignore (will only send filename*);
    - strip accents using unicode's decomposing normalisations,
    which can be done from unicode data (stdlib), and keep only ascii;
    - use the ascii transliteration tables from Unidecode (PyPI);
    - use iso-8859-1
    Ignore is the safest, and can be used to trigger a fallback
    to the document location (which can be percent-encoded utf-8
    if you control the URLs).
    See https://tools.ietf.org/html/rfc6266#appendix-D
    """

    # While this method exists, it could also sanitize the filename
    # by rejecting slashes or other weirdness that might upset a receiver.

    if disposition != 'attachment':
        assert is_token(disposition)

    rv = disposition

    if is_token(filename):
        rv += '; filename=%s' % (filename, )
        return rv
    elif is_ascii(filename) and is_lws_safe(filename):
        qd_filename = qd_quote(filename)
        rv += '; filename="%s"' % (qd_filename, )
        if qd_filename == filename:
            # RFC 6266 claims some implementations are iffy on qdtext's
            # backslash-escaping, we'll include filename* in that case.
            return rv
    elif filename_compat:
        if is_token(filename_compat):
            rv += '; filename=%s' % (filename_compat, )
        else:
            assert is_lws_safe(filename_compat)
            rv += '; filename="%s"' % (qd_quote(filename_compat), )

    # alnum are already considered always-safe, but the rest isn't.
    # Python encodes ~ when it shouldn't, for example.
    rv += "; filename*=utf-8''%s" % (percent_encode(
        filename, safe=attr_chars_nonalnum, encoding='utf-8'), )

    # This will only encode filename_compat, if it used non-ascii iso-8859-1.
    return rv.encode('iso-8859-1')
