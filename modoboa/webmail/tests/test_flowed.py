"""Tests for plain text messages in format=flowed (RFC 3676)."""

from django.core import mail
from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import flowed
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

LONG_LINE = (
    "This paragraph is long enough to be cut into several lines when the "
    "message is sent, so that it stays readable everywhere."
)


class EncodeTestCase(SimpleTestCase):

    def test_long_lines_are_cut_at_spaces(self):
        lines = flowed.encode(LONG_LINE).split("\n")
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(line) <= flowed.WIDTH for line in lines))
        # Soft breaks: every line but the last ends with a space
        self.assertTrue(all(line.endswith(" ") for line in lines[:-1]))
        self.assertFalse(lines[-1].endswith(" "))

    def test_trailing_spaces_are_removed(self):
        """They would turn hard breaks into soft ones."""
        self.assertEqual(flowed.encode("Hello  \nWorld"), "Hello\nWorld")

    def test_signature_separator_is_kept(self):
        self.assertEqual(flowed.encode("Hi\n-- \nJohn"), "Hi\n-- \nJohn")

    def test_space_stuffing(self):
        self.assertEqual(
            flowed.encode(" indented\nFrom here"), "  indented\n From here"
        )

    def test_quotes(self):
        self.assertEqual(
            flowed.encode("> quoted\n>> older\n>\nmine"),
            "> quoted\n>> older\n>\nmine",
        )
        lines = flowed.encode(f"> {LONG_LINE}").split("\n")
        self.assertTrue(all(line.startswith("> ") for line in lines))

    def test_long_word(self):
        word = "x" * 100
        self.assertEqual(flowed.encode(f"{word} end"), f"{word} \nend")


class DecodeTestCase(SimpleTestCase):

    def test_round_trip(self):
        text = (
            f"{LONG_LINE}\n\n> {LONG_LINE}\n>> older\n  indented\n"
            "From here\n-- \nJohn"
        )
        self.assertEqual(flowed.decode(flowed.encode(text)), text)

    def test_soft_breaks_are_joined(self):
        self.assertEqual(flowed.decode("Hello \nworld\nNext"), "Hello world\nNext")

    def test_delsp(self):
        self.assertEqual(flowed.decode("Hel \nlo", delsp=True), "Hello")

    def test_quote_depth_change_is_a_hard_break(self):
        self.assertEqual(flowed.decode("> a \nb"), "> a \nb")


class SendFlowedTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _send(self, body, body_format):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        data = {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "subject": "test",
            "body": body,
            "body_format": body_format,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 204)
        return mail.outbox[0].message()

    def _text_part(self, message):
        return next(
            part for part in message.walk() if part.get_content_type() == "text/plain"
        )

    def test_plain_message(self):
        message = self._send(LONG_LINE, "plain")
        part = self._text_part(message)
        self.assertEqual(part.get_param("format"), "flowed")
        text = part.get_payload(decode=True).decode()
        self.assertEqual(flowed.decode(text), LONG_LINE)

    def test_text_part_of_html_message(self):
        message = self._send(f"<p>{LONG_LINE}</p>", "html")
        part = self._text_part(message)
        self.assertEqual(part.get_param("format"), "flowed")
        self.assertEqual(
            flowed.decode(part.get_payload(decode=True).decode()), LONG_LINE
        )
