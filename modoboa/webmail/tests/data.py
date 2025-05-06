# flake8: noqa

"""Tests data."""

BODYSTRUCTURE_SAMPLE_1 = [
    b"36 (FLAGS (\\Seen))",
    b'36 (UID 36 BODYSTRUCTURE (("text" "plain" ("charset" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 959 29 NIL ("inline" NIL) NIL NIL)("text" "html" ("charset" "UTF-8") NIL NIL "QUOTED-PRINTABLE" 14695 322 NIL ("inline" NIL) NIL NIL) "alternative" ("boundary" "----=_Part_2437867_661044267.1501268072105") NIL NIL NIL))',
]

BODYSTRUCTURE_SAMPLE_2 = [
    (
        b'19 (UID 19 FLAGS (\\Seen $label4 user_flag-1) BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1" "format" "flowed") NIL NIL "7bit" 2 1 NIL NIL NIL NIL)("message" "rfc822" ("name*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74") NIL NIL "8bit" 3632 ("Wed, 13 Dec 2006 20:30:02 +0100" {70}',
        b"[INSCRIPTION] R\xe9c\xe9ption de votre dossier d'inscription Free Haut D\xe9bit",
    ),
    (
        b' (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) ((NIL NIL "hautdebit" "freetelecom.fr")) ((NIL NIL "nguyen.antoine" "wanadoo.fr")) NIL NIL NIL "<20061213193125.9DA0919AC@dgroup2-2.proxad.net>") ("text" "plain" ("charset" "iso-8859-1") NIL NIL "8bit" 1428 38 NIL ("inline" NIL) NIL NIL) 76 NIL ("inline" ("filename*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74")) NIL NIL) "mixed" ("boundary" "------------040706080908000209030901") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {266}',
        b"Date: Tue, 19 Dec 2006 19:50:13 +0100\r\nFrom: Antoine Nguyen <nguyen.antoine@wanadoo.fr>\r\nTo: Antoine Nguyen <tonio@koalabs.org>\r\nSubject: [Fwd: [INSCRIPTION] =?ISO-8859-1?Q?R=E9c=E9ption_de_votre_?=\r\n =?ISO-8859-1?Q?dossier_d=27inscription_Free_Haut_D=E9bit=5D?=\r\n\r\n",
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_3 = [
    (
        b'58 (UID 123753 BODYSTRUCTURE ((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 90 10 NIL NIL NIL NIL)("text" "html" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 1034 33 NIL NIL NIL NIL) "alternative" ("boundary" "_000_HE1PR10MB1642F2B8BA7FF8EAC0FC7AECD86E0HE1PR10MB1642EURP_") NIL NIL NIL)("application" "pdf" ("name" "=?iso-8859-1?Q?CV=5FAude=5FGIRODON=5FNGUYEN=5Fao=FBt2017_g=E9n=E9rique.pd?= =?iso-8859-1?Q?f?=") NIL {95}',
        "=?iso-8859-1?Q?CV=5FAude=5FGIRODON=5FNGUYEN=5Fao=FBt2017_g=E9n=E9rique.pd?=\n =?iso-8859-1?Q?f?=",
    ),
    b' "base64" 94130 NIL ("attachment" ("filename" "=?iso-8859-1?Q?CV=5FAude=5FGIRODON=5FNGUYEN=5Fao=FBt2017_g=E9n=E9rique.pd?= =?iso-8859-1?Q?f?=" "size" "68787" "creation-date" "Wed, 13 Sep 2017 08:50:03 GMT" "modification-date" "Wed, 13 Sep 2017 08:50:03 GMT")) NIL NIL) "mixed" ("boundary" "_004_HE1PR10MB1642F2B8BA7FF8EAC0FC7AECD86E0HE1PR10MB1642EURP_") NIL ("fr-FR") NIL))',
]

BODYSTRUCTURE_4 = b'BODYSTRUCTURE ((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 886 32 NIL NIL NIL NIL)("text" "html" ("charset" "us-ascii") NIL NIL "quoted-printable" 1208 16 NIL NIL NIL NIL) "alternative" ("boundary" "----=_NextPart_001_0003_01CCC564.B2F64FF0") NIL NIL NIL)("application" "octet-stream" ("name" "Carte Verte_2.pdf") NIL NIL "base64" 285610 NIL ("attachment" ("filename" "Carte Verte_2.pdf")) NIL NIL) "mixed" ("boundary" "----=_NextPart_000_0002_01CCC564.B2F64FF0") NIL NIL NIL)'

BODYSTRUCTURE_SAMPLE_4 = [
    (
        b"855 (UID 46931 "
        + BODYSTRUCTURE_4
        + b" BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT REPLY-TO MESSAGE-ID)] {235}",
        b"From: <Service.client10@maaf.fr>\r\nTo: <TONIO@NGYN.ORG>\r\nCc: \r\nSubject: Notre contact du 28/12/2011 - 192175092\r\nDate: Wed, 28 Dec 2011 13:29:17 +0100\r\nMessage-ID: <CABY0dkJspTaFn7v-1OG1nc9M0Qxn+VUTpcXzxyGNBnSnZtqMrw@mail.gmail.com>\r\n\r\n",
    ),
    b")",
]

BODYSTRUCTURE_ONLY_4 = [(b"855 (UID 46931 " + BODYSTRUCTURE_4), ")"]

BODYSTRUCTURE_ONLY_5 = [(b"855 (UID 46932 " + BODYSTRUCTURE_4), ")"]

BODY_PLAIN_4 = [
    (b"855 (UID 46931 BODY[1.1] {25}", b"This is a test message.\r\n"),
    b")",
]

BODYSTRUCTURE_SAMPLE_5 = [
    (
        b'856 (UID 46936 BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 724 22 NIL NIL NIL NIL)("text" "html" ("charset" "ISO-8859-1") NIL NIL "quoted-printable" 2662 48 NIL NIL NIL NIL) "alternative" ("boundary" "----=_Part_1326887_254624357.1325083973970") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {258}',
        "Date: Wed, 28 Dec 2011 15:52:53 +0100 (CET)\r\nFrom: =?ISO-8859-1?Q?Malakoff_M=E9d=E9ric?= <communication@communication.malakoffmederic.com>\r\nTo: Antoine Nguyen <tonio@ngyn.org>\r\nSubject: =?ISO-8859-1?Q?Votre_inscription_au_grand_Jeu_Malakoff_M=E9d=E9ric?=\r\n\r\n",
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_6 = [
    (
        b'123 (UID 3 BODYSTRUCTURE (((("text" "plain" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 1266 30 NIL NIL NIL NIL)("text" "html" ("charset" "iso-8859-1") NIL NIL "quoted-printable" 8830 227 NIL NIL NIL NIL) "alternative" ("boundary" "_000_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_") NIL NIL NIL)("image" "png" ("name" "image005.png") "<image005.png@01CC6CAA.4FADC490>" "image005.png" "base64" 7464 NIL ("inline" ("filename" "image005.png" "size" "5453" "creation-date" "Tue, 06 Sep 2011 13:33:49 GMT" "modification-date" "Tue, 06 Sep 2011 13:33:49 GMT")) NIL NIL)("image" "jpeg" ("name" "image006.jpg") "<image006.jpg@01CC6CAA.4FADC490>" "image006.jpg" "base64" 2492 NIL ("inline" ("filename" "image006.jpg" "size" "1819" "creation-date" "Tue, 06 Sep 2011 13:33:49 GMT" "modification-date" "Tue, 06 Sep 2011 13:33:49 GMT")) NIL NIL) "related" ("boundary" "_006_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_" "type" "multipart/alternative") NIL NIL NIL)("application" "pdf" ("name" "bilan assurance CIC.PDF") NIL "bilan assurance CIC.PDF" "base64" 459532 NIL ("attachment" ("filename" "bilan assurance CIC.PDF" "size" "335811" "creation-date" "Fri, 16 Sep 2011 12:45:23 GMT" "modification-date" "Fri, 16 Sep 2011 12:45:23 GMT")) NIL NIL)(("text" "plain" ("charset" "utf-8") NIL NIL "quoted-printable" 1389 29 NIL NIL NIL NIL)("text" "html" ("charset" "utf-8") NIL NIL "quoted-printable" 1457 27 NIL NIL NIL NIL) "alternative" ("boundary" "===============0775904800==") ("inline" NIL) NIL NIL) "mixed" ("boundary" "_007_152AC7ECD1F8AB43A9AD95DBDDCA3118082C09GKIMA24cmcicfr_") NIL ("fr-FR") NIL)',
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_7 = [
    (
        b'856 (UID 11111 BODYSTRUCTURE ((("text" "plain" ("charset" "UTF-8") NIL NIL "7bit" 0 0 NIL NIL NIL NIL) "mixed" ("boundary" "----=_Part_407172_3159001.1321948277321") NIL NIL NIL)("application" "octet-stream" ("name" "26274308.pdf") NIL NIL "base64" 14906 NIL ("attachment" ("filename" "(26274308.pdf")) NIL NIL) "mixed" ("boundary" "----=_Part_407171_9686991.1321948277321") NIL NIL NIL)',
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_8 = [
    (
        b'1 (UID 947 BODYSTRUCTURE ("text" "html" ("charset" "utf-8") NIL NIL "8bit" 889 34 NIL NIL NIL NIL) BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT)] {80}',
        "From: Antoine Nguyen <tonio@ngyn.org>\r\nDate: Sat, 26 Mar 2016 11:45:49 +0100\r\n\r\n",
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_9 = [
    (
        b"855 (UID 46932 "
        + BODYSTRUCTURE_4
        + b" BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT)] {235}",
        b"From: <Service.client10@maaf.fr>\r\nTo: <TONIO@NGYN.ORG>\r\nCc: \r\nSubject: Notre contact du 28/12/2011 - 192175092\r\nDate: Wed, 28 Dec 2011 13:29:17 +0100\r\nMessage-ID: <CABY0dkJspTaFn7v-1OG1nc9M0Qxn+VUTpcXzxyGNBnSnZtqMrw@mail.gmail.com>\r\n\r\n",
    ),
    b")",
]

BODYSTRUCTURE_SAMPLE_10 = [
    (
        b"855 (UID 46932 " + BODYSTRUCTURE_4 + b" BODY[1.1] {10})",
        b"XXXXXXXX\r\n",
        b"BODY[2] {10}",
        b"XXXXXXXX\r\n",
        b")",
    )
]

BODYSTRUCTURE_SAMPLE_WITH_FLAGS = [
    (
        b'19 (UID 19 FLAGS (\\Seen) RFC822.SIZE 100000 BODYSTRUCTURE (("text" "plain" ("charset" "ISO-8859-1" "format" "flowed") NIL NIL "7bit" 2 1 NIL NIL NIL NIL)("message" "rfc822" ("name*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74") NIL NIL "8bit" 3632 ("Wed, 13 Dec 2006 20:30:02 +0100" {70}',  # noqa
        b"[INSCRIPTION] R\xe9c\xe9ption de votre dossier d'inscription Free Haut D\xe9bit",
    ),  # noqa
    (
        b' (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) (("Free Haut Debit" NIL "inscription" "freetelecom.fr")) ((NIL NIL "hautdebit" "freetelecom.fr")) ((NIL NIL "nguyen.antoine" "wanadoo.fr")) NIL NIL NIL "<20061213193125.9DA0919AC@dgroup2-2.proxad.net>") ("text" "plain" ("charset" "iso-8859-1") NIL NIL "8bit" 1428 38 NIL ("inline" NIL) NIL NIL) 76 NIL ("inline" ("filename*" "ISO-8859-1\'\'%5B%49%4E%53%43%52%49%50%54%49%4F%4E%5D%20%52%E9%63%E9%70%74%69%6F%6E%20%64%65%20%76%6F%74%72%65%20%64%6F%73%73%69%65%72%20%64%27%69%6E%73%63%72%69%70%74%69%6F%6E%20%46%72%65%65%20%48%61%75%74%20%44%E9%62%69%74")) NIL NIL) "mixed" ("boundary" "------------040706080908000209030901") NIL NIL NIL) BODY[HEADER.FIELDS (DATE FROM TO CC SUBJECT)] {266}',  # noqa
        b"Date: Tue, 19 Dec 2006 19:50:13 +0100\r\nFrom: Antoine Nguyen <nguyen.antoine@wanadoo.fr>\r\nTo: Antoine Nguyen <tonio@koalabs.org>\r\nSubject: [Fwd: [INSCRIPTION] =?ISO-8859-1?Q?R=E9c=E9ption_de_votre_?=\r\n =?ISO-8859-1?Q?dossier_d=27inscription_Free_Haut_D=E9bit=5D?=\r\n\r\n",
    ),
    b")",
]

EMPTY_BODYSTRUCTURE = 'BODYSTRUCTURE (("text" "plain" ("charset" "us-ascii") NIL NIL "quoted-printable" 0 0 NIL NIL NIL NIL)("application" "zip" ("name" "hotmail.com!ngyn.org!1435428000!1435514400.zip") NIL NIL "base64" 978 NIL ("attachment" ("filename" "hotmail.com!ngyn.org!1435428000!1435514400.zip")) NIL NIL) "mixed" ("boundary" "--boundary_32281_b52cf564-2a50-4f96-aeb0-ef5f83b05463") NIL NIL NIL)'

BODYSTRUCTURE_EMPTY_MAIL = [bytes(f"33 (UID 33 {EMPTY_BODYSTRUCTURE})", "utf-8")]

BODYSTRUCTURE_EMPTY_MAIL_WITH_HEADERS = [
    (
        bytes(f"33 (UID 33 {EMPTY_BODYSTRUCTURE}", "utf-8")
        + b" BODY[HEADER.FIELDS (FROM TO CC DATE SUBJECT)] {235}",
        b"From: <Service.client10@maaf.fr>\r\nTo: <TONIO@NGYN.ORG>\r\nCc: \r\nSubject: Notre contact du 28/12/2011 - 192175092\r\nDate: Wed, 28 Dec 2011 13:29:17 +0100\r\nMessage-ID: <CABY0dkJspTaFn7v-1OG1nc9M0Qxn+VUTpcXzxyGNBnSnZtqMrw@mail.gmail.com>\r\n\r\n",
    ),
    b")",
]

EMPTY_BODY = [(b"33 (UID 33 BODY[1] {0}", b""), b")"]

BODYSTRUCTURE_WITH_PDF = [
    (
        b'1000 (UID 3444 BODYSTRUCTURE (("text" "plain" ("charset" "utf-8") NIL NIL "7BIT" 123 4 NIL NIL NIL)("application" "pdf" ("name" "file.pdf") NIL NIL "base64" 789 NIL ("attachment" ("filename" "file.pdf")) NIL NIL) "mixed" ("boundary" "--boundary_32281_b52cf564-2a50-4f96-aeb0-ef5f83b05463") NIL NIL NIL) BODY[2] {752}',
        b"JVBERi0xLjQKJcfsj6IKMSAwIG9iago8PC9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlIC9QYWdlcwovS2lkcyBbMyAwIFJdCi9Db3VudCAxCj4+CmVuZG9iagozIDAgb2JqCjw8L1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovUmVzb3VyY2VzIDw8L0ZvbnQgPDwKL0YxIDQgMCBSCj4+Cj4+Ci9Db250ZW50cyA1IDAgUgo+PgplbmRvYmoKNSAwIG9iago8PC9MZW5ndGggNzYKc3RyZWFtCkJUIApIZWxsbyBXb3JsZCENCkVUCmVuZHN0cmVhbQplbmRvYmoKNCAwIG9iago8PC9UeXBlIC9Gb250Ci9TdWJ0eXBlIC9UcnVlVHlwZQovTmFtZSAvRjEKL0Jhc2VGb250IC9IZWx2ZXRpY2ENCj4+CmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDEgMDAwMDAgbiAKMDAwMDAwMDA2MCAwMDAwMCBuIAowMDAwMDAwMTIyIDAwMDAwIG4gCjAwMDAwMDAyMzAgMDAwMDAgbiAKMDAwMDAwMDM0MCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDYKL1Jvb3QgMSAwIFIKL0luZm8gNiAwIFIKPj4Kc3RhcnR4cmVmCjQ1MwolJUVPRgo=",
    ),
    b")",
]

COMPLETE_MAIL = [
    (
        b"109 (UID 133872 BODY[] {2504}",
        b"Return-Path: <test1@test.org>\r\nDelivered-To: test1@test.org\r\nReceived: from mail.testsrv.org\r\n\tby nelson.ngyn.org (Dovecot) with LMTP id E9jPFPHHe1u1bQAABvoInA\r\n\tfor <test1@test.org>; Tue, 21 Aug 2018 10:06:09 +0200\r\nReceived: from [192.168.0.12] (unknown [109.9.172.169])\r\n\t(using TLSv1.2 with cipher ECDHE-RSA-AES256-GCM-SHA384 (256/256 bits))\r\n\t(No client certificate requested)\r\n\tby mail.testsrv.org (Postfix) with ESMTPSA id 2B279E00D2\r\n\tfor <test1@test.org>; Tue, 21 Aug 2018 10:06:09 +0200 (CEST)\r\nDKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=test.org; s=test;\r\n\tt=1534838769; h=from:from:sender:reply-to:subject:subject:date:date:\r\n\t message-id:message-id:to:to:cc:mime-version:mime-version:\r\n\t content-type:content-type:\r\n\t content-transfer-encoding:content-transfer-encoding:in-reply-to:\r\n\t references; bh=EVfAHeUMDygbJe0SkMWJHjgXGjtiTLZnMQbyWqzsrCY=;\r\n\tb=fRc4i+WbPkbdD1BNfV9TqsZZ9nTbnHn6CKbH4nwrQnmUYQvvFUcpXC8PBURyglyLBAqPKb\r\n\tF6Dq7TnvcYdkIpR0XyMko+XB/qt8Wj0J0tC8bFxfknN8yNqj32SQAjtLrsjtzEgC1LkcLo\r\n\tcXU+FQbZR0D8EL7YD/nnsbO4mYnf3as=\r\nTo: Antoine Nguyen <test1@test.org>\r\nFrom: Antoine Nguyen <test1@test.org>\r\nSubject: Simple message\r\nMessage-ID: <7ed6e950-9e2b-b0fc-9e66-5b8358453b8d@test.org>\r\nDate: Tue, 21 Aug 2018 10:06:08 +0200\r\nUser-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101\r\n Thunderbird/52.9.1\r\nMIME-Version: 1.0\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: 7bit\r\nContent-Language: fr-FR\r\nARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=test.org;\r\n\ts=test; t=1534838769; h=from:from:sender:reply-to:subject:subject:date:date:\r\n\t message-id:message-id:to:to:cc:mime-version:mime-version:\r\n\t content-type:content-type:\r\n\t content-transfer-encoding:content-transfer-encoding:in-reply-to:\r\n\t references; bh=EVfAHeUMDygbJe0SkMWJHjgXGjtiTLZnMQbyWqzsrCY=;\r\n\tb=ZV1ndumHftEnhq8Z7zujDS9WUlpJmjrTIEzXsIy8+1HhZ6AEcmur5r8SmS/xfUvpoScNvF\r\n\tlYAHIdbKPX54Fpq7rZVgIhuy8vfcRGprHxH9DMhk3kHiuZLsJT1F6UdPwTYSGAWBTbg1u2\r\n\tHu2VoeSYBV5PrsINvPr1QCbo+GqTlJU=\r\nARC-Seal: i=1; s=test; d=test.org; t=1534838769; a=rsa-sha256; cv=none;\r\n\tb=CE7Q0SnkLMHx82eOtanv4pCtl3fhaPqOAYb3Nqxi5lqwDcO80vTMfGUwOv6r3Exv9Cnj3+nCxejzXtrO4TTKesL9bamOBf+veRYTLfy8wjRIfgEVXS/amOjf9u4UzGgwxL1HbhHWbCIqJhaVwrPZaHZwA9XPmboqGVQNP3i2nH0=\r\nARC-Authentication-Results: i=1; ORIGINATING;\r\n\tauth=pass smtp.auth=test1@test.org smtp.mailfrom=test1@test.org\r\nAuthentication-Results: ORIGINATING;\r\n\tauth=pass smtp.auth=test1@test.org smtp.mailfrom=test1@test.org\r\n\r\nHello!\r\n\r\n",
    ),
    b")",
]
