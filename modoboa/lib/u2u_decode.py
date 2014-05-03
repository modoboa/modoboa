#!/usr/bin/env python
# coding: utf-8
"""
u2u_decode.py

unstructured rfc2047 header to unicode
"""
import re
from email.header import decode_header, make_header

# check spaces between encoded_words (and strip them)
sre = re.compile(r'\?=[ \t]+=\?')
# re pat for MIME encoded_word (without trailing spaces)
mre = re.compile(r'=\?[^?]*?\?[bq]\?[^?\t]*?\?=', re.I)


def clean_spaces(m):
    """Replace unencoded spaces in string

    :param str m: a match object
    :return: the cleaned string
    """
    return m.group(0).replace(" ", "=20")


def decode_mime(m):
    """substitute matching encoded_word with unicode equiv.
    """
    h = decode_header(clean_spaces(m))
    try:
        u = unicode(make_header(h))
    except UnicodeDecodeError:
        return m.group(0)
    return u


def u2u_decode(s):
    ur"""utility function for (final) decoding of mime header

    note: resulting string is in one line (no \n within)
    note2: spaces between enc_words are stripped (see RFC2047)

    >>> u2u_decode('=?ISO-8859-15?Q?=20Profitez de tous les services en ligne sur impots.gouv.fr?=')
    u' Profitez de tous les services en ligne sur impots.gouv.fr'
    >>> u2u_decode('=?ISO-8859-1?Q?Accus=E9?= de =?ISO-8859-1?Q?r=E9ception?= de votre annonce')
    u'Accus\xe9 de r\xe9ception de votre annonce'
    >>> u2u_decode('Sm=?ISO-8859-1?B?9g==?=rg=?ISO-8859-1?B?5Q==?=sbord')
    u'Sm\xf6rg\xe5sbord'
    """
    s = ''.join(s.splitlines())
    s = sre.sub('?==?', s)
    u = mre.sub(decode_mime, s)
    return u
