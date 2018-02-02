# -*- coding: utf-8 -*-

"""Tests for u2u_decode."""

from __future__ import unicode_literals

from django.test import TestCase

from .. import u2u_decode


class U2UTestCase(TestCase):
    """Test RFC1342 decoding utilities."""

    def test_header_decoding(self):
        """Simple decoding."""
        samples = [
            ("=?ISO-8859-15?Q?=20Profitez de tous les services en ligne sur "
             "impots.gouv.fr?=",
             "Profitez de tous les services en ligne sur impots.gouv.fr"),
            ("=?ISO-8859-1?Q?Accus=E9?= de =?ISO-8859-1?Q?r=E9ception?= de "
             "votre annonce",
             "Accusé de réception de votre annonce"),
            ("Sm=?ISO-8859-1?B?9g==?=rg=?ISO-8859-1?B?5Q==?=sbord",
             "Sm\xf6rg\xe5sbord"),
            # The following case currently fails because of the way we split
            # encoded words to parse them separately, which can lead to
            # unexpected unicode decode errors... I think it will work fine on
            # Python3
            # ("=?utf-8?B?VMOpbMOpcMOpYWdlIFZJTkNJIEF1dG9yb3V0ZXMgLSBFeHDD?=\n"
            #  "=?utf-8?B?qWRpdGlvbiBkZSB2b3RyZSBjb21tYW5kZSBOwrAgMjAxNzEyMDcw"
            #  "MDA1?=\n=?utf-8?B?MyBkdSAwNy8xMi8yMDE3IDE0OjQ5OjQx?=",
            #  "")
        ]
        for sample in samples:
            self.assertEqual(u2u_decode.u2u_decode(sample[0]), sample[1])

    def test_address_header_decoding(self):
        """Check address decoding."""
        mailsploit_sample = (
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=00?="
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?=@mailsploit.com")
        expected_result = (
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q??="
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?=@mailsploit.com")
        self.assertEqual(
            u2u_decode.decode_address(mailsploit_sample),
            ("", expected_result)
        )
        mailsploit_sample = (
            '"=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=0A=00?="\n'
            "<=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q?=0A=00?="
            "@mailsploit.com>")
        expected_result = (
            "potus@whitehouse.gov",
            "=?utf-8?b?cG90dXNAd2hpdGVob3VzZS5nb3Y=?==?utf-8?Q??="
            "@mailsploit.com")
        self.assertEqual(
            u2u_decode.decode_address(mailsploit_sample),
            expected_result)
