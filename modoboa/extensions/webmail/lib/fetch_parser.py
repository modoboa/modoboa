# coding: utf-8
"""
:mod:`fetch_parser` --- Simple parser for FETCH responses
---------------------------------------------------------

The ``imaplib`` module doesn't parse IMAP responses, it returns raw
values. This is pretty annoying when one FETCH command is issued to
retrieve multiple attributes of a message.

This simple module tries to fix that *problem*.
"""


class ParseError(Exception):
    pass


class Token(object):

    def __init__(self, value):
        self.value = value


class Literal(Token):

    def __init__(self, value):
        super(Literal, self).__init__(value)
        self.next_token_len = int(self.value[1:-1])


def parse_next_token(buf):
    """Look for the next *token*

    By *token*, I mean: *literal*, *quoted* or anything else until the
    next ' ' or ')' character (number, NIL and others should fall into
    this last category).

    :param buf: the buffer to parse
    :return: the position of the token's last caracter into ``buf``
    """
    end = -1
    klass = Token
    if buf[0] == '{':
        # Literal
        end = buf.find('}')
        klass = Literal
    elif buf[0] == '"':
        # quoted
        end = buf.find('"', 1)
    else:
        for pos, c in enumerate(buf):
            if c in [' ', ')']:
                end = pos - 1
                break
        if end == -1:
            raise ParseError(
                "End of buffer reached while looking for a token end")
    end += 1
    token = klass(buf[:end])
    return token, end


def parse_bodystructure(buf, depth=0, prefix=""):
    """Special parser for BODYSTRUCTURE response

    This function tries to transform a BODYSTRUCTURE response sent by
    the server into the corresponding list structure.

    :param buf: the buffer to parse
    :return: a list object and the position of the last scanned
             character into ``buf``
    """
    ret = []
    pos = 1  # skip the first ')'
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
                newret = [ret.pop(-1), subret]
                ret.append(newret)
            else:
                ret[-1].append(subret)
            pos += end + 1
            nb_bodystruct += 1
            continue

        if c == ')':
            partnum = None
            if depth:
                # FIXME : the following is buggy because it doesn't
                # make a difference between a content-disposition with
                # multiple args beeing parsed and a mime part! (see
                # the last example at the end of the file)
                if isinstance(ret[0], list) or len(ret) >= 7:
                    partnum = prefix
            if partnum is not None:
                return [{"partnum": partnum, "struct": ret}], pos
            return ret, pos
        if c == ' ':
            pos += 1
            continue
        nb_bodystruct = 0
        token, end = parse_next_token(buf[pos:])
        pos += end
        if isinstance(token, Literal):
            ret.append(buf[pos:pos + token.next_token_len].strip('"'))
            pos += token.next_token_len
        else:
            ret.append(token.value.strip('"'))

    raise ParseError(
        "End of buffer reached while looking for a BODY/BODYSTRUCTURE end")


def parse_fetch_response(data):
    """Parse a FETCH response, previously issued by a UID command

    We extract the message number, the UID and its value and consider
    what remains as the response data.

    :param data: the data returned by the ``imaplib`` command
    :return: a dictionnary
    """
    result = {}
    cpt = 0
    while cpt < len(data):
        content = ()
        while cpt < len(data) and data[cpt] != ')':
            if isinstance(data[cpt], str):
                # FIXME : probably an unsolicited response
                cpt += 1
                continue
            content += data[cpt]
            cpt += 1
        cpt += 1

        buf = "".join(content)
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
                instring = False
                for pos, c in enumerate(response):
                    if not instring and c == '"':
                        instring = True
                        continue
                    if instring and c == '"':
                        if pos and response[pos - 1] != '\\':
                            instring = False
                            continue
                    if not instring and c == '(':
                        parendepth += 1
                        continue
                    if not instring and c == ')':
                        parendepth -= 1
                        if parendepth == 0:
                            end = pos + 1
                            break
            else:
                token, end = parse_next_token(response)
                if isinstance(token, Literal):
                    response = response[end:]
                    end = token.next_token_len

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
    if isinstance(bs[0], dict):
        print "%s :" % bs[0]["partnum"],
        struct = bs[0]["struct"]
    else:
        struct = bs

    if isinstance(struct[0], list):
        print "multipart/%s" % struct[1]
        for part in struct[0]:
            dump_bodystructure(part, depth + 1)
    else:
        print "%s/%s" % (struct[0], struct[1])


if __name__ == "__main__":
#    resp = [('855 (UID 46931 BODYSTRUCTURE ((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 886 32 NIL NIL NIL NIL)("text" "html" ("charset" "us-ascii") NIL NIL "quoted-printable" 1208 16 NIL NIL NIL NIL) "alternative" ("boundary" "----=_NextPart_001_0003_01CCC564.B2F64FF0") NIL NIL NIL)("application" "octet-stream" ("name" "Carte Verte_2.pdf") NIL NIL "base64" 285610 NIL ("attachment" ("filename" "Carte Verte_2.pdf")) NIL NIL) "mixed" ("boundary" "----=_NextPart_000_0002_01CCC564.B2F64FF0") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {153}', 'From: <Service.client10@maaf.fr>\r\nTo: <TONIO@NGYN.ORG>\r\nCc: \r\nSubject: Notre contact du 28/12/2011 - 192175092\r\nDate: Wed, 28 Dec 2011 13:29:17 +0100\r\n\r\n'), ')']

#    resp = [('856 (UID 46936 BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 724 22 NIL NIL NIL NIL)("text" "html" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 2662 48 NIL NIL NIL NIL) "alternative" ("boundary" "----=_Part_1326887_254624357.1325083973970") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {258}', 'Date: Wed, 28 Dec 2011 15:52:53 +0100 (CET)\r\nFrom: =?ISO-8859-1?Q?Malakoff_M=E9d=E9ric?= <communication@communication.malakoffmederic.com>\r\nTo: Antoine Nguyen <tonio@ngyn.org>\r\nSubject: =?ISO-8859-1?Q?Votre_inscription_au_grand_Jeu_Malakoff_M=E9d=E9ric?=\r\n\r\n'), ')']

    resp = [
        ('856 (UID 11111 BODYSTRUCTURE ((("text" "plain" ("charset" "UTF-8") NIL NIL "7bit" 0 0 NIL NIL NIL NIL) "mixed" ("boundary" "----=_Part_407172_3159001.1321948277321") NIL NIL NIL)("application" "octet-stream" ("name" "26274308.pdf") NIL NIL "base64" 14906 NIL ("attachment" ("filename" "26274308.pdf")) NIL NIL) "mixed" ("boundary" "----=_Part_407171_9686991.1321948277321") NIL NIL NIL)',
         ),
        ')']

#    resp = [('19 (UID 19 FLAGS (\\Seen) BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1" "format" "flowed") NIL NIL "7bit" 2 1 NIL NIL NIL NIL)("message" "rfc822" ("name*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74") NIL NIL "8bit" 3632 ("Wed, 13 Dec 2006 20:30:02 +0100" {70}',
#  "[INSCRIPTION] R\xe9c\xe9ption de votre dossier d'inscription Free Haut D\xe9bit"),
#            (' (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) ((NIL NIL "hautdebit" "freetelecom.fr")) ((NIL NIL "nguyen.antoine" "wanadoo.fr")) NIL NIL NIL "<20061213193125.9DA0919AC@dgroup2-2.proxad.net>") ("text" "plain" ("charset" "iso-8859-1") NIL NIL "8bit" 1428 38 NIL ("inline" NIL) NIL NIL) 76 NIL ("inline" ("filename*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74")) NIL NIL) "mixed" ("boundary" "------------040706080908000209030901") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {266}',
#             'Date: Tue, 19 Dec 2006 19:50:13 +0100\r\nFrom: Antoine Nguyen <nguyen.antoine@wanadoo.fr>\r\nTo: Antoine Nguyen <tonio@koalabs.org>\r\nSubject: [Fwd: [INSCRIPTION] =?ISO-8859-1?Q?R=E9c=E9ption_de_votre_?=\r\n =?ISO-8859-1?Q?dossier_d=27inscription_Free_Haut_D=E9bit=5D?=\r\n\r\n'), ')']

    # resp = [('123 (UID 3 BODYSTRUCTURE (((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 1266 30 NIL NIL NIL NIL)("text" "html" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 8830 227 NIL NIL NIL NIL) "alternative" ("boundary" "_000_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_") NIL NIL NIL)("image" "png" ("name" "image005.png") "<image005.png@01CC6CAA.4FADC490>" "image005.png" "base64" 7464 NIL ("inline" ("filename" "image005.png" "size" "5453" "creation-date" "Tue, 06 Sep 2011 13:33:49 GMT" "modification-date" "Tue, 06 Sep 2011 13:33:49 GMT")) NIL NIL)("image" "jpeg" ("name" "image006.jpg") "<image006.jpg@01CC6CAA.4FADC490>" "image006.jpg" "base64" 2492 NIL ("inline" ("filename" "image006.jpg" "size" "1819" "creation-date" "Tue, 06 Sep 2011 13:33:49 GMT" "modification-date" "Tue, 06 Sep 2011 13:33:49 GMT")) NIL NIL) "related" ("boundary" "_006_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_" "type" "multipart/alternative") NIL NIL NIL)("application" "pdf" ("name" "bilan assurance CIC.PDF") NIL "bilan assurance CIC.PDF" "base64" 459532 NIL ("attachment" ("filename" "bilan assurance CIC.PDF" "size" "335811" "creation-date" "Fri, 16 Sep 2011 12:45:23 GMT" "modification-date" "Fri, 16 Sep 2011 12:45:23 GMT")) NIL NIL)(("text" "plain" ("charset" "utf-8") NIL NIL "quoted-printable" 1389 29 NIL NIL NIL NIL)("text" "html" ("charset" "utf-8") NIL NIL "quoted-printable" 1457 27 NIL NIL NIL NIL) "alternative" ("boundary" "===============0775904800==") ("inline" NIL) NIL NIL) "mixed" ("boundary" "_007_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_") NIL ("fr-FR") NIL)',), ')']

    # resp = [('856 (UID 11111 BODYSTRUCTURE ((("text" "plain" ("charset" "UTF-8") NIL NIL "7bit" 0 0 NIL NIL NIL NIL) "mixed" ("boundary" "----=_Part_407172_3159001.1321948277321") NIL NIL NIL)("application" "octet-stream" ("name" "26274308.pdf") NIL NIL "base64" 14906 NIL ("attachment" ("filename" "(26274308.pdf")) NIL NIL) "mixed" ("boundary" "----=_Part_407171_9686991.1321948277321") NIL NIL NIL)',), ')']

    print parse_fetch_response(resp)
