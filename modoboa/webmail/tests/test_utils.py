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
