"""Tests for the conversion of a body when the format of the editor changes."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import utils
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

REPLY = (
    ">John Doe wrote:\n>L'equipe <dev> & co\n>Second line\n>\n>> deeper\n\n"
    "My answer\n  indented\n\n---\nSig line"
)


class PlainText2HtmlTestCase(SimpleTestCase):

    def test_paragraphs_and_line_breaks(self):
        self.assertEqual(
            utils.plaintext2html("One\nTwo\n\n\nThree"),
            "<p>One<br>Two</p><p>Three</p>",
        )

    def test_quotes_and_escaping(self):
        self.assertEqual(
            utils.plaintext2html(REPLY),
            "<blockquote><p>John Doe wrote:<br>L&#x27;equipe &lt;dev&gt; &amp; co"
            "<br>Second line</p><blockquote><p>deeper</p></blockquote></blockquote>"
            "<p>My answer<br>&nbsp;&nbsp;indented</p><p>---<br>Sig line</p>",
        )

    def test_round_trip(self):
        self.assertEqual(
            utils.html2plaintext(utils.plaintext2html(REPLY)),
            "> John Doe wrote:\n> L'equipe <dev> & co\n> Second line\n>\n>> deeper"
            "\n\nMy answer\n  indented\n\n---\nSig line",
        )

    def test_empty_content(self):
        self.assertEqual(utils.plaintext2html(""), "")


class ConvertBodyTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.authenticate()
        self.url = reverse("v2:webmail-compose-session-convert")

    def _convert(self, body, source, target):
        return self.client.post(
            self.url,
            {"body": body, "source_format": source, "target_format": target},
            format="json",
        )

    def test_html_to_plain(self):
        """The text is the one sent as the text part of HTML messages."""
        body = "<p>Hello <b>world</b></p><ul><li><p>a</p></li></ul>"
        response = self._convert(body, "html", "plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["body"], utils.html2plaintext(body))
        self.assertEqual(response.json()["body"], "Hello world\n\n- a")

    def test_plain_to_html(self):
        response = self._convert("> quoted\n\n mine", "plain", "html")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["body"],
            "<blockquote><p>quoted</p></blockquote><p>&nbsp;mine</p>",
        )

    def test_same_format(self):
        response = self._convert("  kept as is  ", "plain", "plain")
        self.assertEqual(response.json()["body"], "  kept as is  ")

    def test_empty_body(self):
        response = self._convert("", "html", "plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["body"], "")

    def test_invalid_format(self):
        response = self._convert("x", "markdown", "plain")
        self.assertEqual(response.status_code, 400)
        self.assertIn("source_format", response.json())
