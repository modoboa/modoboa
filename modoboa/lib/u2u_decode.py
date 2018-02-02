# -*- coding: utf-8 -*-

"""
Unstructured rfc2047 header to unicode.

A stupid (and not accurate) answer to https://bugs.python.org/issue1079.

"""

from __future__ import unicode_literals

import re
from email.header import decode_header, make_header
from email.utils import parseaddr

from django.utils.encoding import smart_text

# check spaces between encoded_words (and strip them)
sre = re.compile(r"\?=[ \t]+=\?")
# re pat for MIME encoded_word (without trailing spaces)
mre = re.compile(r"=\?[^?]*?\?[bq]\?[^?\t]*?\?=", re.I)
# re do detect encoded ASCII characters
ascii_re = re.compile(r"=[\dA-F]{2,3}", re.I)


def clean_spaces(m):
    """Replace unencoded spaces in string.

    :param str m: a match object
    :return: the cleaned string
    """
    return m.group(0).replace(" ", "=20")


def clean_non_printable_char(m):
    """Strip non printable characters."""
    code = int(m.group(0)[1:], 16)
    if code < 20:
        return ""
    return m.group(0)


def decode_mime(m):
    """Substitute matching encoded_word with unicode equiv."""
    h = decode_header(clean_spaces(m))
    try:
        u = smart_text(make_header(h))
    except (LookupError, UnicodeDecodeError):
        return m.group(0)
    return u


def clean_header(header):
    """Clean header function."""
    header = "".join(header.splitlines())
    header = sre.sub("?==?", header)
    return ascii_re.sub(clean_non_printable_char, header)


def u2u_decode(s):
    """utility function for (final) decoding of mime header

    note: resulting string is in one line (no \n within)
    note2: spaces between enc_words are stripped (see RFC2047)
    """
    return mre.sub(decode_mime, clean_header(s)).strip(" \r\t\n")


def decode_address(value):
    """Special function for address decoding.

    We need a dedicated processing because RFC1342 explicitely says
    address MUST NOT contain encoded-word:

      These are the ONLY locations where an encoded-word may appear.  In
      particular, an encoded-word MUST NOT appear in any portion of an
      "address".  In addition, an encoded-word MUST NOT be used in a
      Received header field.
    """
    phrase, address = parseaddr(clean_header(value))
    if phrase:
        phrase = mre.sub(decode_mime, phrase)
    return phrase, address
