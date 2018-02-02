# -*- coding: iso-8859-1 -*-

"""
Imap folder names are encoded using a special version of utf-7 as
defined in RFC 2060 section 5.1.3.

5.1.3.  Mailbox International Naming Convention

   By convention, international mailbox names are specified using a
   modified version of the UTF-7 encoding described in [UTF-7].  The
   purpose of these modifications is to correct the following problems
   with UTF-7:

      1) UTF-7 uses the "+" character for shifting; this conflicts with
         the common use of "+" in mailbox names, in particular USENET
         newsgroup names.

      2) UTF-7's encoding is BASE64 which uses the "/" character; this
         conflicts with the use of "/" as a popular hierarchy delimiter.

      3) UTF-7 prohibits the unencoded usage of "\"; this conflicts with
         the use of "\" as a popular hierarchy delimiter.

      4) UTF-7 prohibits the unencoded usage of "~"; this conflicts with
         the use of "~" in some servers as a home directory indicator.

      5) UTF-7 permits multiple alternate forms to represent the same
         string; in particular, printable US-ASCII chararacters can be
         represented in encoded form.

   In modified UTF-7, printable US-ASCII characters except for "&"
   represent themselves; that is, characters with octet values 0x20-0x25
   and 0x27-0x7e.  The character "&" (0x26) is represented by the two-
   octet sequence "&-".

   All other characters (octet values 0x00-0x1f, 0x7f-0xff, and all
   Unicode 16-bit octets) are represented in modified BASE64, with a
   further modification from [UTF-7] that "," is used instead of "/".
   Modified BASE64 MUST NOT be used to represent any printing US-ASCII
   character which can represent itself.

   "&" is used to shift to modified BASE64 and "-" to shift back to US-
   ASCII.  All names start in US-ASCII, and MUST end in US-ASCII (that
   is, a name that ends with a Unicode 16-bit octet MUST end with a "-
   ").

      For example, here is a mailbox name which mixes English, Japanese,
      and Chinese text: ~peter/mail/&ZeVnLIqe-/&U,BTFw-

Found here:
http://svn.plone.org/svn/collective/mxmImapClient/trunk/imapUTF7.py

"""
from __future__ import print_function, unicode_literals

import codecs

# encoding

PRINTABLE = set(range(0x20, 0x26)) | set(range(0x27, 0x7f))


def modified_utf7(s):
    s_utf7 = s.encode("utf-7")
    return s_utf7[1:-1].replace(b"/", b",")


def doB64(_in, r):  # NOQA:N802
    if _in:
        r.extend([b"&", modified_utf7("".join(_in)), b"-"])
        del _in[:]


def encoder(s):
    r = []
    _in = []
    for c in s:
        if ord(c) in PRINTABLE:
            doB64(_in, r)
            r.append(c.encode())
        elif c == "&":
            doB64(_in, r)
            r.append(b"&-")
        else:
            _in.append(c)
    doB64(_in, r)
    return (b"".join(r), len(s))


# decoding


def modified_unutf7(s):
    s_utf7 = b"+" + s.replace(b",", b"/") + b"-"
    return s_utf7.decode("utf-7")


def decoder(s):
    r = []
    decoded = bytearray()
    for c in s:
        if c == ord("&") and not decoded:
            decoded.append(ord("&"))
        elif c == ord("-") and decoded:
            if len(decoded) == 1:
                r.append("&")
            else:
                r.append(modified_unutf7(decoded[1:]))
            decoded = bytearray()
        elif decoded:
            decoded.append(c)
        else:
            r.append(chr(c))
    if decoded:
        r.append(modified_unutf7(decoded[1:]))
    bin_str = "".join(r)
    return (bin_str, len(s))


class StreamReader(codecs.StreamReader):
    def decode(self, s, errors="strict"):
        return decoder(s)


class StreamWriter(codecs.StreamWriter):
    def decode(self, s, errors="strict"):
        return encoder(s)


def imap4_utf_7(name):
    if name == "imap4-utf-7":
        return (encoder, decoder, StreamReader, StreamWriter)


codecs.register(imap4_utf_7)


# testing methods

def imapUTF7Encode(ust):  # NOQA:N802
    "Returns imap utf-7 encoded version of string"
    return ust.encode("imap4-utf-7")


def imapUTF7EncodeSequence(seq):  # NOQA:N802
    "Returns imap utf-7 encoded version of strings in sequence"
    return [imapUTF7Encode(itm) for itm in seq]


def imapUTF7Decode(st):  # NOQA:N802
    "Returns utf7 encoded version of imap utf-7 string"
    return st.decode("imap4-utf-7")


def imapUTF7DecodeSequence(seq):  # NOQA:N802
    "Returns utf7 encoded version of imap utf-7 strings in sequence"
    return [imapUTF7Decode(itm) for itm in seq]


def utf8Decode(st):  # NOQA:N802
    "Returns utf7 encoded version of imap utf-7 string"
    return st.decode("utf-8")


def utf7SequenceToUTF8(seq):  # NOQA:N802
    "Returns utf7 encoded version of imap utf-7 strings in sequence"
    return [itm.decode("imap4-utf-7").encode("utf-8") for itm in seq]


__all__ = ["imapUTF7Encode", "imapUTF7Decode", ]

if __name__ == "__main__":

    # print 'bøx'.encode('imap4-utf-7')
    # print 'expected b&APg-x'

    # print 'båx'.encode('imap4-utf-7')
    # print 'expected b&AOU-x'

    print("#######")
    print("bøx")
    e = imapUTF7Encode("bøx")
    print(e)
    print(imapUTF7Decode(e).encode("latin-1"))

    print("#######")
    print("båx")
    e = imapUTF7Encode("båx")
    print(e)
    print(imapUTF7Decode(e).encode("latin-1"))

    print("#######")
    print("~/bågø")
    e = imapUTF7Encode("~/bågø")
    print(e)
    print(imapUTF7Decode(e).encode("latin-1"))

    print("#######")
    print("Ting & Såger")
    e = imapUTF7Encode("Ting & Såger")
    print(e)
    print(imapUTF7Decode(e).encode("latin-1"))

    # e = imapUTF7Decode('b&AOU-x')
    # print e.encode('latin-1')

    # e = imapUTF7Decode('b&APg-x')
    # print e.encode('latin-1')

    print("#######")
    print("~/Følder/mailbåx & stuff + more")
    n = "~/Følder/mailbåx & stuff + more"
    e = imapUTF7Encode(n)
    print(e)
    print(imapUTF7Decode(e).encode("latin-1"))

    print("#######")
    print("~peter/mail/&ZeVnLIqe-/&U,BTFw-")
    print(imapUTF7Decode("~peter/mail/&ZeVnLIqe-/&U,BTFw-").encode("utf-8"))
