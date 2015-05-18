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
import binascii
import codecs

# encoding


def modified_base64(s):
    s = s.encode('utf-16be')
    return binascii.b2a_base64(s).rstrip('\n=').replace('/', ',')


def doB64(_in, r):
    if _in:
        r.append('&%s-' % modified_base64(''.join(_in)))
        del _in[:]


def encoder(s):
    r = []
    _in = []
    for c in s:
        ordC = ord(c)
        if 0x20 <= ordC <= 0x25 or 0x27 <= ordC <= 0x7e:
            doB64(_in, r)
            r.append(c)
        elif c == '&':
            doB64(_in, r)
            r.append('&-')
        else:
            _in.append(c)
    doB64(_in, r)
    return (str(''.join(r)), len(s))


# decoding

def modified_unbase64(s):
    b = binascii.a2b_base64(s.replace(',', '/') + '===')
    return unicode(b, 'utf-16be')


def decoder(s):
    r = []
    decode = []
    for c in s:
        if c == '&' and not decode:
            decode.append('&')
        elif c == '-' and decode:
            if len(decode) == 1:
                r.append('&')
            else:
                r.append(modified_unbase64(''.join(decode[1:])))
            decode = []
        elif decode:
            decode.append(c)
        else:
            r.append(c)
    if decode:
        r.append(modified_unbase64(''.join(decode[1:])))
    bin_str = ''.join(r)
    return (bin_str, len(s))


class StreamReader(codecs.StreamReader):
    def decode(self, s, errors='strict'):
        return decoder(s)


class StreamWriter(codecs.StreamWriter):
    def decode(self, s, errors='strict'):
        return encoder(s)


def imap4_utf_7(name):
    if name == 'imap4-utf-7':
        return (encoder, decoder, StreamReader, StreamWriter)
codecs.register(imap4_utf_7)


# testing methods

def imapUTF7Encode(ust):
    "Returns imap utf-7 encoded version of string"
    return ust.encode('imap4-utf-7')


def imapUTF7EncodeSequence(seq):
    "Returns imap utf-7 encoded version of strings in sequence"
    return [imapUTF7Encode(itm) for itm in seq]


def imapUTF7Decode(st):
    "Returns utf7 encoded version of imap utf-7 string"
    return st.decode('imap4-utf-7')


def imapUTF7DecodeSequence(seq):
    "Returns utf7 encoded version of imap utf-7 strings in sequence"
    return [imapUTF7Decode(itm) for itm in seq]


def utf8Decode(st):
    "Returns utf7 encoded version of imap utf-7 string"
    return st.decode('utf-8')


def utf7SequenceToUTF8(seq):
    "Returns utf7 encoded version of imap utf-7 strings in sequence"
    return [itm.decode('imap4-utf-7').encode('utf-8') for itm in seq]


__all__ = ['imapUTF7Encode', 'imapUTF7Decode', ]

if __name__ == '__main__':

    # print u'bøx'.encode('imap4-utf-7')
    # print 'expected b&APg-x'

    # print u'båx'.encode('imap4-utf-7')
    # print 'expected b&AOU-x'

    print '#######'
    print 'bøx'
    e = imapUTF7Encode(u'bøx')
    print e
    print imapUTF7Decode(e).encode('latin-1')

    print '#######'
    print 'båx'
    e = imapUTF7Encode(u'båx')
    print e
    print imapUTF7Decode(e).encode('latin-1')

    print '#######'
    print '~/bågø'
    e = imapUTF7Encode(u'~/bågø')
    print e
    print imapUTF7Decode(e).encode('latin-1')

    print '#######'
    print 'Ting & Såger'
    e = imapUTF7Encode(u'Ting & Såger')
    print e
    print imapUTF7Decode(e).encode('latin-1')

    # e = imapUTF7Decode('b&AOU-x')
    # print e.encode('latin-1')

    # e = imapUTF7Decode('b&APg-x')
    # print e.encode('latin-1')

    print '#######'
    print '~/Følder/mailbåx & stuff + more'
    n = u'~/Følder/mailbåx & stuff + more'
    e = imapUTF7Encode(n)
    print e
    print imapUTF7Decode(e).encode('latin-1')

    print '#######'
    print '~peter/mail/&ZeVnLIqe-/&U,BTFw-'
    print imapUTF7Decode('~peter/mail/&ZeVnLIqe-/&U,BTFw-').encode('utf-8')
