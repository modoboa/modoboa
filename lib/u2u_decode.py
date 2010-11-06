#!/usr/bin/env python
# u2u_decode.py
# unstructured rfc2047 header to unicode
#
import re
from email.header import decode_header, make_header

# check spaces between encoded_words (and strip them)
sre = re.compile(r'\?=[ \t]+=\?')
# re pat for MIME encoded_word (without trailing spaces)
mre = re.compile(r'=\?[^?]*?\?[bq]\?[^? \t]*?\?=', re.I)

def decode_mime(m):
    # substitute matching encoded_word with unicode equiv.
    h = decode_header(m.group(0))
    u = unicode(make_header(h))
    return u

def u2u_decode(s):
    # utility function for (final) decoding of mime header
    # note: resulting string is in one line (no \n within)
    # note2: spaces between enc_words are stripped (see RFC2047)
    s = ''.join(s.splitlines())
    s = sre.sub('?==?', s)
    u = mre.sub(decode_mime, s)
    return u

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        s = sys.argv[1]
    else:
        s = """[Apache-Users 7784] ServerAlias =?ISO-2022-JP?B?GyRAGyRCJEsbKEI=?=:(
 =?ISO-2022-JP?B?GyRCJTMlbSVzGyhC?=)=?ISO-2022-JP?B?GyRCJHI7SBsoQg==?=
 =?ISO-2022-JP?B?GyRAGyRCTVEkOSRrJEg1c0YwJCwkKiQrJDckJBsoQg==?="""
        s = 'Sm=?ISO-8859-1?B?9g==?=rg=?ISO-8859-1?B?5Q==?=sbord'
    u = u2u_decode(s)
    print u

