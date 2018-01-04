# -*- coding: utf-8 -*-

"""Tests for email_utils."""

from __future__ import unicode_literals

import os

from django.test import SimpleTestCase
from django.utils.encoding import smart_bytes, smart_text

from ..email_utils import Email

SAMPLES_DIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "sample_messages"))


class EmailTestImplementation(Email):

    def _fetch_message(self):
        message_path = os.path.join(SAMPLES_DIR, "%s-input.txt" % self.mailid)
        assert os.path.isfile(message_path), "%s does not exist." % message_path

        with open(message_path, "rb") as fp:
            mail_text = smart_bytes(fp.read())

        return mail_text


class EmailTests(SimpleTestCase):
    """Tests for modoboa.lib.email_utils.Email

    When writing new sample messages use the following naming convention for
    the sample files stored in sample_messages:

    input:  {message_id}-input.txt
    output: {message_id}-output-{dformat}_{no,}links.txt
    """

    def _get_expected_output(self, message_id, **kwargs):
        ext = kwargs["dformat"] if "dformat" in kwargs else "plain"
        ext += "_links" if "links" in kwargs and kwargs["links"] else "_nolinks"
        message_path = os.path.join(SAMPLES_DIR,
                                    "%s-output-%s.txt" % (message_id, ext))
        assert os.path.isfile(message_path), "%s does not exist." % message_path

        with open(message_path, "rb") as fp:
            # output should always be unicode (py2) or str (py3)
            mail_text = smart_text(fp.read())

        return mail_text

    def _test_email(self, message_id, **kwargs):
        """Boiler plate code for testing e-mails."""
        expected_output = self._get_expected_output(message_id, **kwargs)
        output = EmailTestImplementation(message_id, **kwargs).body
        self.assertEqual(output, expected_output)

    def test_invalid_links_value(self):
        """modoboa-amavis set links = "0"; in python "0" == True, fixed in PR 79
           https://github.com/modoboa/modoboa-amavis/pull/79"""
        with self.assertRaises(TypeError) as cm:
            EmailTestImplementation("text_plain", links="0")

            ex_message = cm.exception.messages
            self.assertEqual(ex_message,
                             "links == \"0\" is not valid, did you mean True or "
                             "False?")

    def test_links_value_for_webmail(self):
        """modoboa-webmail sets links = 0 or 1
           TODO: this should be fixed in modoboa-webmail to use True/False"""
        email = EmailTestImplementation("text_plain", links=0)
        self.assertFalse(email.links)

        email = EmailTestImplementation("text_plain", links=1)
        self.assertTrue(email.links)

    def test_headers(self):
        email = EmailTestImplementation("text_plain")
        # test header names are case insensative
        self.assertEqual(email.msg["x-upper-case-header"], "FOOBAR")
        self.assertEqual(email.msg["X-Lower-Case-Header"], "foobar")
        self.assertEqual(email.msg["x-random-case-header"], "fOoBaR")

        expected_output = [
            {"name": "From", "value": "Someone <someone@example.net>"},
            {"name": "To", "value": "Me <me@example.net>"},
            {"name": "Cc", "value": ""},
            {"name": "Date", "value": "Sun, 17 Dec 2017 13:10:14 +0000"},
            {"name": "Subject", "value": "Tést message"},
        ]
        self.assertEqual(email.headers, expected_output)

    def test_email_text_plain(self):
        self._test_email("text_plain")

    def test_email_multipart_as_text(self):
        """display the text/plain part of a multipart message"""
        self._test_email("multipart")

    def test_email_multipart_with_links(self):
        """display the text/html part of a multipart message"""
        self._test_email("multipart", dformat="html", links=True)

    def test_email_multipart_without_links(self):
        """display the text/html part of a multipart message with links removed"""
        self._test_email("multipart", dformat="html", links=False)
