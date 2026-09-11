"""Tests for inline images handling in ImapEmail."""

import base64
import os
import tempfile
from unittest import mock

from django.test import SimpleTestCase, override_settings

from modoboa.webmail.lib.imapemail import ImapEmail
from modoboa.webmail.lib.imaputils import BodyStructure
from modoboa.webmail.lib.fetch_parser import FetchResponseParser
from modoboa.webmail.tests import data as tests_data

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


def _make_email(inlines, links=True):
    email = ImapEmail.__new__(ImapEmail)
    email.links = links
    email.mailid = "3"
    email.mbox = "INBOX"
    email.bs = mock.Mock(inlines=inlines)
    email.imapc = mock.Mock()
    email.imapc.fetchpart.return_value = (
        None,
        base64.b64encode(PNG_BYTES).decode(),
    )
    return email


class InlineImagesTestCase(SimpleTestCase):
    def test_bodystructure_inlines_have_content_type(self):
        parsed = FetchResponseParser().parse(tests_data.BODYSTRUCTURE_SAMPLE_6)
        bs = BodyStructure(parsed[3]["BODYSTRUCTURE"])
        self.assertEqual(
            bs.inlines["image005.png@01CC6CAA.4FADC490"]["Content-Type"], "image/png"
        )
        self.assertEqual(
            bs.inlines["image006.jpg@01CC6CAA.4FADC490"]["Content-Type"],
            "image/jpeg",
        )

    def test_inline_image_embedded_as_data_uri(self):
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            }
        )
        with tempfile.TemporaryDirectory() as workdir:
            with override_settings(MEDIA_ROOT=workdir):
                email._fetch_inlines()
                # Nothing must be written to the (public) media directory
                self.assertEqual(os.listdir(workdir), [])
        expected = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode()
        self.assertEqual(email._map_cid("cid:img@x"), expected)
        self.assertEqual(email._map_cid("CID:img%40x"), expected)

    def test_unsafe_inline_types_ignored(self):
        email = _make_email(
            {
                "svg@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/svg+xml",
                },
                "html@x": {
                    "pnum": "3",
                    "encoding": "base64",
                    "Content-Type": "text/html",
                },
            }
        )
        email._fetch_inlines()
        email.imapc.fetchpart.assert_not_called()
        self.assertEqual(email._map_cid("cid:svg@x"), "cid:svg@x")
        self.assertEqual(email._map_cid("cid:html@x"), "cid:html@x")

    def test_inlines_not_fetched_without_links(self):
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            },
            links=False,
        )
        email._fetch_inlines()
        email.imapc.fetchpart.assert_not_called()

    def test_other_urls_untouched(self):
        email = _make_email({})
        url = "https://example.com/a.png"
        self.assertEqual(email._map_cid(url), url)
