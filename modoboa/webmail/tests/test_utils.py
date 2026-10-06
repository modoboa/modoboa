"""Tests for webmail lib utilities."""

import base64
import os
import tempfile

from django.conf import settings
from django.test import SimpleTestCase

from modoboa.webmail.lib import utils

# A minimal valid 1x1 PNG.
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgAAACAAFUok"
    "+fAAAAAElFTkSuQmCC"
)


class MakeBodyImagesInlineTestCase(SimpleTestCase):
    """Tests for make_body_images_inline (path traversal protection)."""

    def test_local_image_is_inlined(self):
        """An image stored under BASE_DIR is embedded as a MIME part."""
        fd, path = tempfile.mkstemp(suffix=".png", dir=settings.BASE_DIR)
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(PNG_BYTES)
            rel = os.path.relpath(path, settings.BASE_DIR)
            body = f'<div><img src="/{rel}"></div>'
            html, parts = utils.make_body_images_inline(body)
            self.assertEqual(len(parts), 1)
            self.assertIn("cid:", html)
            self.assertNotIn(rel, html)
        finally:
            os.unlink(path)

    def test_traversal_image_is_rejected(self):
        """A ../ traversal pointing outside BASE_DIR is not read."""
        fd, path = tempfile.mkstemp(suffix=".png")
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(PNG_BYTES)
            # Build a traversal from BASE_DIR back up to the absolute path.
            rel = os.path.relpath(path, settings.BASE_DIR)
            self.assertTrue(rel.startswith(".."))
            body = f'<div><img src="/{rel}"></div>'
            html, parts = utils.make_body_images_inline(body)
            self.assertEqual(parts, [])
            # The src must be left untouched (no cid rewrite).
            self.assertNotIn("cid:", html)
        finally:
            os.unlink(path)

    def test_encoded_traversal_image_is_rejected(self):
        """A percent-encoded traversal is also rejected."""
        fd, path = tempfile.mkstemp(suffix=".png")
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(PNG_BYTES)
            rel = os.path.relpath(path, settings.BASE_DIR)
            encoded = rel.replace("../", "%2e%2e%2f")
            body = f'<div><img src="/{encoded}"></div>'
            html, parts = utils.make_body_images_inline(body)
            self.assertEqual(parts, [])
        finally:
            os.unlink(path)

    def test_non_image_file_does_not_crash(self):
        """A non-image file under BASE_DIR is skipped, not fatal."""
        fd, path = tempfile.mkstemp(suffix=".txt", dir=settings.BASE_DIR)
        try:
            with os.fdopen(fd, "wb") as fp:
                fp.write(b"not an image")
            rel = os.path.relpath(path, settings.BASE_DIR)
            body = f'<div><img src="/{rel}"></div>'
            html, parts = utils.make_body_images_inline(body)
            self.assertEqual(parts, [])
        finally:
            os.unlink(path)

    def test_remote_url_is_ignored(self):
        """Remote image URLs are left untouched."""
        body = '<div><img src="https://example.test/x.png"></div>'
        html, parts = utils.make_body_images_inline(body)
        self.assertEqual(parts, [])
        self.assertIn("https://example.test/x.png", html)


class Html2PlainTextTestCase(SimpleTestCase):
    def test_text_around_inline_elements(self):
        self.assertEqual(
            utils.html2plaintext("<p>Hello <b>world</b> again, <i>see</i> this.</p>"),
            "Hello world again, see this.",
        )

    def test_paragraphs_and_line_breaks(self):
        self.assertEqual(
            utils.html2plaintext("<p>One<br>Two<br><br>Three</p><div>Four</div>"),
            "One\nTwo\n\nThree\n\nFour",
        )

    def test_whitespace_is_collapsed(self):
        self.assertEqual(
            utils.html2plaintext("<p>\n  Hello\n   world  </p>"), "Hello world"
        )

    def test_preformatted_text(self):
        self.assertEqual(
            utils.html2plaintext("<pre>a\n  b</pre><p>c</p>"), "a\n  b\n\nc"
        )

    def test_links(self):
        self.assertEqual(
            utils.html2plaintext(
                '<p><a href="https://example.test">site</a> '
                '<a href="https://example.test">https://example.test</a> '
                '<a href="mailto:a@example.test">a@example.test</a></p>'
            ),
            "site <https://example.test> https://example.test a@example.test",
        )

    def test_lists(self):
        self.assertEqual(
            utils.html2plaintext(
                "<ul><li>a</li><li>b<ol><li>c</li><li>d</li></ol></li></ul>"
            ),
            "- a\n- b\n  1. c\n  2. d",
        )

    def test_list_item_paragraphs(self):
        """Rich text editors put the content of list items into paragraphs."""
        self.assertEqual(
            utils.html2plaintext(
                "<ul><li><p>a</p></li><li><p>b</p><p>c</p>"
                "<ul><li><p>d</p></li></ul></li></ul><p>End</p>"
            ),
            "- a\n- b\nc\n  - d\n\nEnd",
        )

    def test_non_breaking_spaces_are_kept(self):
        self.assertEqual(
            utils.html2plaintext("<p>&nbsp;&nbsp;indented&nbsp; text</p>"),
            "  indented  text",
        )

    def test_quotes(self):
        self.assertEqual(
            utils.html2plaintext(
                "<p>Answer</p><blockquote><p>One</p><p>Two</p></blockquote><p>End</p>"
            ),
            "Answer\n\n> One\n>\n> Two\n\nEnd",
        )

    def test_hidden_content(self):
        self.assertEqual(
            utils.html2plaintext(
                "<html><head><title>T</title><style>p {}</style></head>"
                "<body><p>Text</p><script>alert(1)</script>tail<!-- c --> end"
                "</body></html>"
            ),
            "Text\n\ntail end",
        )

    def test_image_alternative_text(self):
        self.assertEqual(
            utils.html2plaintext('<p>Logo: <img src="x.png" alt="ACME"></p>'),
            "Logo: ACME",
        )

    def test_empty_content(self):
        self.assertEqual(utils.html2plaintext(""), "")
        self.assertEqual(utils.html2plaintext("   "), "")
        self.assertEqual(utils.html2plaintext("<!-- c -->"), "")


class DataUriImagesTestCase(SimpleTestCase):
    """Images of the editor given as data: URIs become parts of the message."""

    def _uri(self, content_type="image/png", payload=PNG_BYTES):
        return f"data:{content_type};base64,{base64.b64encode(payload).decode()}"

    def test_data_uri_becomes_a_part(self):
        body = f'<p><img src="{self._uri()}"></p>'
        html, parts = utils.make_body_images_inline(body)
        self.assertEqual(len(parts), 1)
        cid = parts[0]["Content-ID"].strip("<>")
        self.assertIn(f'src="cid:{cid}"', html)
        self.assertNotIn("data:", html)
        self.assertEqual(parts[0].get_content_type(), "image/png")
        self.assertEqual(parts[0].get_payload(decode=True), PNG_BYTES)

    def test_same_image_attached_once(self):
        uri = self._uri()
        html, parts = utils.make_body_images_inline(
            f'<p><img src="{uri}"><img src="{uri}"></p>'
        )
        self.assertEqual(len(parts), 1)

    def test_invalid_images_are_ignored(self):
        for uri in (
            self._uri("image/svg+xml", b"<svg/>"),
            self._uri("text/html", b"<p>x</p>"),
            "data:image/png;base64,",
        ):
            with self.subTest(uri=uri[:30]):
                html, parts = utils.make_body_images_inline(f'<p><img src="{uri}"></p>')
                self.assertEqual(parts, [])
