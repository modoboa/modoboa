"""Tests for the two independent switches of the message viewer."""

from django.test import SimpleTestCase

from modoboa.lib.email_utils import Email

BODY = (
    '<p><a href="https://example.test/page">link</a>'
    '<img src="https://example.test/tracker.gif">'
    '<img src="cid:img@x"></p>'
)


class LinksAndImagesTestCase(SimpleTestCase):
    """Links and images can be enabled one without the other."""

    def _render(self, links, images):
        email = Email("1", links=links, images=images)
        email._images = {"img@x": "data:image/png;base64,AAA="}
        return email._post_process_html(BODY)

    def test_nothing_enabled(self):
        content = self._render(links=False, images=False)
        self.assertNotIn("https://example.test/page", content)
        self.assertNotIn("tracker.gif", content)

    def test_images_only(self):
        content = self._render(links=False, images=True)
        # The tracker and the inline image are loaded...
        self.assertIn("tracker.gif", content)
        self.assertIn("data:image/png;base64,AAA=", content)
        # ... but the link is still dropped
        self.assertNotIn("https://example.test/page", content)

    def test_links_only(self):
        content = self._render(links=True, images=False)
        self.assertIn("https://example.test/page", content)
        self.assertNotIn("tracker.gif", content)
        self.assertNotIn("data:image/png;base64,AAA=", content)

    def test_everything_enabled(self):
        content = self._render(links=True, images=True)
        self.assertIn("https://example.test/page", content)
        self.assertIn("tracker.gif", content)
        self.assertIn("data:image/png;base64,AAA=", content)

    def test_images_default_to_the_links_setting(self):
        self.assertTrue(Email("1", links=True).images)
        self.assertFalse(Email("1", links=False).images)
