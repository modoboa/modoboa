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


def _make_email(inlines, links=True, images=None):
    email = ImapEmail.__new__(ImapEmail)
    email.links = links
    email.images = links if images is None else images
    email.mailid = "3"
    email.mbox = "INBOX"
    email.bs = mock.Mock(inlines=inlines)
    # MagicMock: ImapEmail.__del__ calls imapc.__exit__()
    email.imapc = mock.MagicMock()
    email.imapc.fetch_parts.side_effect = lambda uid, mbox, pnums: {
        pnum: base64.b64encode(PNG_BYTES).decode() for pnum in pnums
    }
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
        email.imapc.fetch_parts.assert_not_called()
        self.assertEqual(email._map_cid("cid:svg@x"), "cid:svg@x")
        self.assertEqual(email._map_cid("cid:html@x"), "cid:html@x")

    def test_inlines_fetched_without_images(self):
        """Embedded images don't wait for the remote ones."""
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            },
            images=False,
        )
        email._fetch_inlines()
        email.imapc.fetch_parts.assert_called_once()

    def test_inlines_not_embedded_into_replies(self):
        """A reply would carry them as data: URIs."""
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            },
            images=False,
        )
        email.embed_inlines = False
        email._fetch_inlines()
        email.imapc.fetch_parts.assert_not_called()

    def test_inlines_fetched_without_links(self):
        """Images are displayed even when the links stay disabled."""
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            },
            links=False,
            images=True,
        )
        email._fetch_inlines()
        email.imapc.fetch_parts.assert_called_once()

    def test_only_referenced_inlines_fetched(self):
        """Images the content doesn't show are listed, not downloaded."""
        email = _make_email(
            {
                cid: {
                    "pnum": pnum,
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
                for cid, pnum in (("a@x", "2"), ("b@x", "3"), ("c@x", "4"))
            }
        )
        email._fetch_inlines({"a@x", "c@x"})
        # A single command for every image
        email.imapc.fetch_parts.assert_called_once_with("3", "INBOX", ["2", "4"])
        self.assertTrue(email._map_cid("cid:a@x").startswith("data:image/png"))
        self.assertEqual(email._map_cid("cid:b@x"), "cid:b@x")

    def test_other_urls_untouched(self):
        email = _make_email({})
        url = "https://example.com/a.png"
        self.assertEqual(email._map_cid(url), url)


class RemoteContentTestCase(SimpleTestCase):
    """Remote resources are dropped, and reported, until images are displayed."""

    HTML = (
        '<div><img src="cid:img@x"><img src="https://tracker.example/p.gif">'
        '<a href="https://example.com/">link</a></div>'
    )

    def _process(self, images, html=None):
        email = _make_email(
            {
                "img@x": {
                    "pnum": "2",
                    "encoding": "base64",
                    "Content-Type": "image/png",
                }
            },
            images=images,
        )
        email._fetch_inlines()
        return email, email._post_process_html(html or self.HTML)

    def test_embedded_images_kept_remote_ones_dropped(self):
        email, html = self._process(images=False)
        self.assertIn("data:image/png;base64,", html)
        self.assertNotIn("tracker.example", html)
        self.assertTrue(email.remote_content_blocked)
        # Links are the reader's other choice, and are left alone
        self.assertIn('href="https://example.com/"', html)

    def test_remote_images_kept_when_displayed(self):
        email, html = self._process(images=True)
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("https://tracker.example/p.gif", html)
        self.assertFalse(email.remote_content_blocked)

    def test_nothing_blocked_without_remote_content(self):
        email, html = self._process(
            images=False,
            html='<div><img src="cid:img@x"><a href="https://example.com/">l</a></div>',
        )
        self.assertFalse(email.remote_content_blocked)

    def test_remote_styles_are_remote_content(self):
        email, html = self._process(
            images=False,
            html="<div style=\"background: url('//cdn.example/bg.png')\">text</div>",
        )
        self.assertNotIn("cdn.example", html)
        self.assertTrue(email.remote_content_blocked)
