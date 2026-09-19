"""Tests for the sorting of message parts into contents, inlines and attachments."""

from unittest import mock

from django.test import SimpleTestCase

from modoboa.webmail.lib.fetch_parser import FetchResponseParser
from modoboa.webmail.lib.imapemail import ImapEmail
from modoboa.webmail.lib.imaputils import BodyStructure

PLAIN = '("text" "plain" ("charset" "utf-8") NIL NIL "7bit" 10 1 NIL NIL NIL NIL)'
HTML = '("text" "html" ("charset" "utf-8") NIL NIL "7bit" 20 1 NIL NIL NIL NIL)'
LOGO = (
    '("image" "png" ("name" "logo.png") "<logo@x>" NIL "base64" 100 NIL '
    '("inline" ("filename" "logo.png")) NIL NIL)'
)
PDF = (
    '("application" "pdf" ("name" "doc.pdf") NIL NIL "base64" 1000 NIL '
    '("attachment" ("filename" "doc.pdf")) NIL NIL)'
)


def _multipart(subtype, *parts):
    return "({} {} NIL NIL NIL)".format("".join(parts), f'"{subtype}"')


def _load(structure):
    response = f"1 (UID 1 BODYSTRUCTURE {structure})".encode()
    parsed = FetchResponseParser().parse([response])
    return BodyStructure(parsed[1]["BODYSTRUCTURE"])


def _names(bs):
    return [att["name"] for att in bs.list_attachments()]


class BodyStructureTestCase(SimpleTestCase):
    def test_related_at_top_level(self):
        """The images of a top-level multipart/related are inlines."""
        bs = _load(_multipart("related", _multipart("alternative", PLAIN, HTML), LOGO))
        self.assertEqual(_names(bs), [])
        self.assertIn("logo@x", bs.inlines)
        self.assertEqual(sorted(bs.contents), ["html", "plain"])

    def test_related_html_only_at_top_level(self):
        bs = _load(_multipart("related", HTML, LOGO))
        self.assertEqual(_names(bs), [])
        self.assertIn("logo@x", bs.inlines)

    def test_nested_related(self):
        bs = _load(
            _multipart(
                "mixed",
                _multipart("related", _multipart("alternative", PLAIN, HTML), LOGO),
                PDF,
            )
        )
        self.assertEqual(_names(bs), ["doc.pdf"])
        self.assertIn("logo@x", bs.inlines)

    def test_inline_image_in_mixed(self):
        """Some clients embed images into a multipart/mixed."""
        bs = _load(_multipart("mixed", PLAIN, LOGO, PLAIN))
        self.assertEqual(_names(bs), [])
        self.assertEqual(len(bs.contents["plain"]), 2)

    def test_image_without_content_id(self):
        """Nothing can reference it: it is an attachment."""
        image = (
            '("image" "png" ("name" "pic.png") NIL NIL "base64" 100 NIL '
            '("inline" ("filename" "pic.png")) NIL NIL)'
        )
        bs = _load(_multipart("related", HTML, image))
        self.assertEqual(_names(bs), ["pic.png"])
        self.assertEqual(bs.inlines, {})

    def test_attached_image_in_mixed(self):
        image = (
            '("image" "jpeg" ("name" "photo.jpg") "<photo@x>" NIL "base64" 100 NIL '
            '("attachment" ("filename" "photo.jpg")) NIL NIL)'
        )
        bs = _load(_multipart("mixed", PLAIN, image))
        self.assertEqual(_names(bs), ["photo.jpg"])

    def test_non_image_in_related(self):
        bs = _load(_multipart("related", HTML, PDF))
        self.assertEqual(_names(bs), ["doc.pdf"])

    def test_attached_text_file(self):
        text = (
            '("text" "plain" ("charset" "utf-8" "name" "notes.txt") NIL NIL '
            '"7bit" 30 2 NIL ("attachment" ("filename" "notes.txt")) NIL NIL)'
        )
        bs = _load(_multipart("mixed", PLAIN, text))
        self.assertEqual(_names(bs), ["notes.txt"])
        self.assertEqual(len(bs.contents["plain"]), 1)

    def test_inlines_can_be_downloaded(self):
        bs = _load(_multipart("related", HTML, LOGO))
        self.assertEqual(bs.find_attachment("2")["Content-Type"], "image/png")


class UnreferencedInlinesTestCase(SimpleTestCase):
    def _email(self, mformat):
        email = ImapEmail.__new__(ImapEmail)
        email.mformat = mformat
        email.attachments = {}
        email.bs = _load(_multipart("related", HTML, LOGO, LOGO.replace("logo", "sig")))
        # MagicMock: ImapEmail.__del__ calls imapc.__exit__()
        email.imapc = mock.MagicMock()
        return email

    def test_referenced_inlines_not_listed(self):
        email = self._email("html")
        email._find_unreferenced_inlines(
            '<img src="cid:logo@x"><img src="CID:sig%40x">'
        )
        self.assertEqual(email.attachments, {})

    def test_unreferenced_inline_listed(self):
        email = self._email("html")
        email._find_unreferenced_inlines('<img src="cid:logo@x">')
        self.assertEqual(
            email.attachments,
            {"3": {"name": "sig.png", "size": 100, "content_type": "image/png"}},
        )

    def test_inlines_listed_with_plain_text(self):
        email = self._email("plain")
        email._find_unreferenced_inlines("cid:logo@x")
        self.assertEqual(sorted(email.attachments), ["2", "3"])
