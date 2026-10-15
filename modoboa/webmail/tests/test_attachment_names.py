"""Tests for the decoding of attachment file names."""

from django.test import SimpleTestCase

from modoboa.webmail.lib.imaputils import BodyStructure, decode_mime_parameters


class DecodeMimeParametersTestCase(SimpleTestCase):
    """MIME parameters come in three shapes (RFC 2047 and RFC 2231)."""

    def test_no_parameters(self):
        for definition in (None, [], "NIL"):
            self.assertEqual(decode_mime_parameters(definition), {})

    def test_plain_value(self):
        self.assertEqual(
            decode_mime_parameters(["name", "report.pdf"]), {"name": "report.pdf"}
        )

    def test_rfc2047_encoded_word(self):
        self.assertEqual(
            decode_mime_parameters(["name", "=?utf-8?Q?r=C3=A9sum=C3=A9.pdf?="]),
            {"name": "résumé.pdf"},
        )

    def test_rfc2231_extended_value(self):
        self.assertEqual(
            decode_mime_parameters(["filename*", "UTF-8''r%C3%A9sum%C3%A9.pdf"]),
            {"filename": "résumé.pdf"},
        )

    def test_rfc2231_latin1_value(self):
        self.assertEqual(
            decode_mime_parameters(["filename*", "ISO-8859-1''facture%20d%E9cembre"]),
            {"filename": "facture décembre"},
        )

    def test_rfc2231_split_value(self):
        """A long name is split over numbered sections."""
        self.assertEqual(
            decode_mime_parameters(
                [
                    "filename*0*",
                    "UTF-8''rapport%20d%27",
                    "filename*1*",
                    "intervention%20",
                    "filename*2*",
                    "d%C3%A9taill%C3%A9.pdf",
                ]
            ),
            {"filename": "rapport d'intervention détaillé.pdf"},
        )

    def test_rfc2231_split_sections_are_ordered(self):
        """Sections are assembled by their number, not by their order."""
        self.assertEqual(
            decode_mime_parameters(
                ["filename*1*", "second", "filename*0*", "UTF-8''first-"]
            ),
            {"filename": "first-second"},
        )

    def test_rfc2231_mixed_sections(self):
        """A section says for itself whether it is encoded."""
        self.assertEqual(
            decode_mime_parameters(
                ["filename*0*", "UTF-8''caf%C3%A9-", "filename*1", "menu.txt"]
            ),
            {"filename": "café-menu.txt"},
        )

    def test_rfc2231_split_without_charset(self):
        self.assertEqual(
            decode_mime_parameters(["filename*0", "long-", "filename*1", "name.txt"]),
            {"filename": "long-name.txt"},
        )

    def test_other_parameters_are_kept(self):
        self.assertEqual(
            decode_mime_parameters(["charset", "utf-8", "name", "a.txt"]),
            {"charset": "utf-8", "name": "a.txt"},
        )

    def test_unexpected_values_are_ignored(self):
        self.assertEqual(decode_mime_parameters(["name"]), {})
        self.assertEqual(decode_mime_parameters(["name", None]), {})


class AttachmentNameTestCase(SimpleTestCase):
    """The name of an attachment, as the interface displays it."""

    def _attachment(self, **kwargs):
        structure = BodyStructure()
        structure.attachments = [{"pnum": "2", "size": 10, **kwargs}]
        return structure.list_attachments()[0]

    def test_name_from_content_type(self):
        attachment = self._attachment(params=["name", "report.pdf"])
        self.assertEqual(attachment["name"], "report.pdf")

    def test_name_from_disposition(self):
        attachment = self._attachment(
            disposition=["attachment", ["filename", "invoice.pdf"]]
        )
        self.assertEqual(attachment["name"], "invoice.pdf")

    def test_disposition_wins_over_content_type(self):
        """Content-Disposition names a file, Content-Type names a part."""
        attachment = self._attachment(
            params=["name", "part.bin"],
            disposition=["attachment", ["filename", "invoice.pdf"]],
        )
        self.assertEqual(attachment["name"], "invoice.pdf")

    def test_encoded_name(self):
        attachment = self._attachment(
            disposition=[
                "inline",
                ["filename*", "ISO-8859-1''%5BINSCRIPTION%5D%20R%E9ception"],
            ]
        )
        self.assertEqual(attachment["name"], "[INSCRIPTION] Réception")

    def test_part_without_a_name(self):
        attachment = self._attachment(params="NIL")
        self.assertEqual(attachment["name"], "part_2")
