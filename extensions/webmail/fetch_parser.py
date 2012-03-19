# coding: utf-8
"""
:mod:`fetch_parser` --- Simple parser for FETCH responses
---------------------------------------------------------

The ``imaplib`` module doesn't parse IMAP responses, it returns raw
values. This is pretty annoying when one FETCH command is issued to
retrieve multiple attributes of a message.

This simple module tries to fix that *problem*.
"""

class ParseError(Exception): pass

def parse_next_token(buf):
    """Look for the next *token*

    By *token*, I mean: *literal*, *quoted* or anything else until the
    next ' ' or ')' character (number, NIL and others should fall into
    this last category).

    :param buf: the buffer to parse
    :return: the position of the token's last caracter into ``buf``
    """
    end = -1
    if buf[0] == '{':
        # Literal
        end = buf.find('}')
    elif buf[0] == '"':
        # quoted
        end = buf.find('"', 1)
    else:
        for pos, c in enumerate(buf):
            if c in [' ', ')']:
                end = pos - 1
                break
        if end == -1:
            raise ParseError("End of buffer reached while looking for a token end")
    return end

def parse_bodystructure(buf, depth=0, prefix=""):
    """Special parser for BODYSTRUCTURE response

    This function tries to transform a BODYSTRUCTURE response sent by
    the server into the corresponding list structure.

    :param buf: the buffer to parse
    :return: a list object and the position of the last scanned
             character into ``buf``
    """
    ret = []
    pos = 1 # skip the first ')'
    nb_bodystruct = 0
    pnum = 1
    while pos < len(buf):
        c = buf[pos]
        if c == '(':
            nprefix = "%s.%s" % (prefix, pnum) if prefix != "" else "%s" % pnum
            subret, end = parse_bodystructure(buf[pos:], depth + 1, nprefix)
            pnum += 1
            if nb_bodystruct == 0:
                ret.append(subret)
            elif nb_bodystruct == 1:
                newret = [ret.pop(-1)]
                newret.append(subret)
                ret.append(newret)
            else:
                ret[-1].append(subret)
            pos += end + 1
            nb_bodystruct += 1
            continue

        if c == ')':
            partnum = None
            if depth:
                if type(ret[0]) == list or len(ret) >= 7:
                    partnum = prefix
            if partnum is not None:
                return [dict(partnum=partnum, struct=ret)], pos
            return ret, pos
        if c == ' ':
            pos += 1
            continue
        nb_bodystruct = 0
        end = parse_next_token(buf[pos:])
        ret.append(buf[pos:pos + end + 1].strip('"'))
        pos += end + 1

    raise ParseError("End of buffer reached while looking for a BODY/BODYSTRUCTURE end")

def parse_fetch_response(data):
    """Parse a FETCH response, previously issued by a UID command

    We extract the message number, the UID and its value and consider
    what remains as the response data.
    
    :param data: the data returned by the ``imaplib`` command
    :return: a dictionnary
    """
    result = {}
    for part in data[0:-1]:
        if part == ')':
            continue
        buf = "".join(part)
        parts = buf.split(' ', 3)
        msgdef = result[int(parts[2])] = {}
        response = parts[3]

        while len(response):
            if response.startswith('BODY') and response[4] == '[':
                end = response.find(']', 5)
                if response[end + 1] == '<':
                    end = response.find('>', end + 1)
                end += 1
            else:
                end = response.find(' ')
            cmdname = response[:end]
            response = response[end + 1:]

            end = 0
            if cmdname in ['BODY', 'BODYSTRUCTURE', 'FLAGS']:
                parendepth = 0
                for pos, c in enumerate(response):
                    if c == '(':
                        parendepth += 1
                        continue
                    if c == ')':
                        parendepth -= 1
                        if parendepth == 0:
                            end = pos + 1
                            break
            else:
                end = parse_next_token(response)
                if response[0] == '{':
                    datalen = int(response[1:end])
                    response = response[end + 1:]
                    end = datalen

            msgdef[cmdname] = response[:end]
            response = response[end + 1:]
            try:
                func = globals()["parse_%s" % cmdname.lower()]
                msgdef[cmdname] = func(msgdef[cmdname])[0]
            except KeyError:
                pass

    return result

def dump_bodystructure(bs, depth=0):
    if depth:
        print " " * (depth * 4),
    if type(bs[0]) == dict:
        print "%s :" % bs[0]["partnum"],
        struct = bs[0]["struct"]
    else:
        struct = bs

    if type(struct[0]) == list:
        print "multipart/%s" % struct[1]
        for part in struct[0]:
            dump_bodystructure(part, depth + 1)
    else:
        print "%s/%s" % (struct[0], struct[1])
        

if __name__ == "__main__":
    resp = [('855 (UID 46931 BODYSTRUCTURE ((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 886 32 NIL NIL NIL NIL)("text" "html" ("charset" "us-ascii") NIL NIL "quoted-printable" 1208 16 NIL NIL NIL NIL) "alternative" ("boundary" "----=_NextPart_001_0003_01CCC564.B2F64FF0") NIL NIL NIL)("application" "octet-stream" ("name" "Carte Verte_2.pdf") NIL NIL "base64" 285610 NIL ("attachment" ("filename" "Carte Verte_2.pdf")) NIL NIL) "mixed" ("boundary" "----=_NextPart_000_0002_01CCC564.B2F64FF0") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {153}', 'From: <Service.client10@maaf.fr>\r\nTo: <TONIO@NGYN.ORG>\r\nCc: \r\nSubject: Notre contact du 28/12/2011 - 192175092\r\nDate: Wed, 28 Dec 2011 13:29:17 +0100\r\n\r\n'), ')']

    #resp = [('856 (UID 46936 BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 724 22 NIL NIL NIL NIL)("text" "html" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 2662 48 NIL NIL NIL NIL) "alternative" ("boundary" "----=_Part_1326887_254624357.1325083973970") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {258}', 'Date: Wed, 28 Dec 2011 15:52:53 +0100 (CET)\r\nFrom: =?ISO-8859-1?Q?Malakoff_M=E9d=E9ric?= <communication@communication.malakoffmederic.com>\r\nTo: Antoine Nguyen <tonio@ngyn.org>\r\nSubject: =?ISO-8859-1?Q?Votre_inscription_au_grand_Jeu_Malakoff_M=E9d=E9ric?=\r\n\r\n'), ')']

    resp = [('856 (UID 11111 BODYSTRUCTURE ((("text" "plain" ("charset" "UTF-8") NIL NIL "7bit" 0 0 NIL NIL NIL NIL) "mixed" ("boundary" "----=_Part_407172_3159001.1321948277321") NIL NIL NIL)("application" "octet-stream" ("name" "26274308.pdf") NIL NIL "base64" 14906 NIL ("attachment" ("filename" "26274308.pdf")) NIL NIL) "mixed" ("boundary" "----=_Part_407171_9686991.1321948277321") NIL NIL NIL)'), ')']

    print parse_fetch_response(resp)
