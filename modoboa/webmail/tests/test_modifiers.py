"""Tests for the body of replies and forwards, as loaded into the editor."""

from unittest import mock

from django.urls import reverse

from modoboa.webmail.lib.imapemail import ForwardModifier, ReplyModifier

from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

MESSAGE_HEADERS = (
    b'From: "John Doe" <john@example.test>\r\n'
    b"To: user@test.com\r\n"
    b"Subject: Question\r\n"
    b"Message-ID: <question@example.test>\r\n"
    b"Date: Tue, 15 Sep 2026 10:00:00 +0200\r\n\r\n"
)
PLAIN_MESSAGE = 70
HTML_MESSAGE = 71
PLAIN_BODY = b'L\'equipe <dev> & "co"\nSecond line'
HTML_BODY = (
    b'<p>Hello <b>world</b> &amp; <a href="https://example.test/doc">co</a></p>'
    b"<p>Bye</p>"
)
ATTRIBUTION = "On Sept. 15, 2026, 8 a.m., John Doe wrote:"
BODYSTRUCTURES = {
    PLAIN_MESSAGE: b'BODYSTRUCTURE ("text" "plain" ("charset" "utf-8") NIL NIL "7bit"'
    b" %d 2 NIL NIL NIL NIL)" % len(PLAIN_BODY),
    HTML_MESSAGE: b'BODYSTRUCTURE ("text" "html" ("charset" "utf-8") NIL NIL "7bit"'
    b" %d 1 NIL NIL NIL NIL)" % len(HTML_BODY),
}
BODIES = {PLAIN_MESSAGE: PLAIN_BODY, HTML_MESSAGE: HTML_BODY}


class MessagesMock(IMAP4Mock):
    """Server holding a plain text message and an HTML only one."""

    def uid(self, command, *args):
        if command != "FETCH" or int(args[0]) not in BODYSTRUCTURES:
            return super().uid(command, *args)
        uid = int(args[0])
        prefix = f"1 (UID {uid} ".encode()
        if "HEADER.FIELDS" in args[1]:
            fields = args[1][args[1].index("(", 1) : args[1].index(")") + 1]
            item = f" BODY[HEADER.FIELDS {fields}] {{{len(MESSAGE_HEADERS)}}}"
            return "OK", [
                (prefix + BODYSTRUCTURES[uid] + item.encode(), MESSAGE_HEADERS),
                b")",
            ]
        if args[1] == "(BODYSTRUCTURE)":
            return "OK", [prefix + BODYSTRUCTURES[uid], b")"]
        content = BODIES[uid]
        return "OK", [(prefix + f"BODY[1] {{{len(content)}}}".encode(), content), b")"]


class ModifierContentTestCase(WebmailTestCase):
    """Body of a reply or a forward, as loaded into the editor."""

    def setUp(self):
        super().setUp()
        self.mock_imap4.return_value = MessagesMock()
        self.authenticate()

    def _content(self, mailid, context, dformat=None):
        url = reverse("v2:webmail-email-content")
        params = {"mailbox": "INBOX", "mailid": mailid, "context": context}
        if dformat:
            params["dformat"] = dformat
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _set_preferences(self, editor, displaymode):
        self.user.parameters.set_value("editor", editor)
        self.user.parameters.set_value("displaymode", displaymode)
        self.user.save()

    def test_reply_in_editor_format(self):
        """The editor format applies, not the display one."""
        self._set_preferences(editor="html", displaymode="plain")
        content = self._content(PLAIN_MESSAGE, "reply")
        self.assertEqual(content["body_format"], "html")
        self.assertIn("<br>", content["body"])

        self._set_preferences(editor="plain", displaymode="html")
        content = self._content(HTML_MESSAGE, "reply")
        self.assertEqual(content["body_format"], "plain")
        self.assertNotIn("<p>", content["body"])

    def test_forward_in_editor_format(self):
        self._set_preferences(editor="html", displaymode="plain")
        content = self._content(PLAIN_MESSAGE, "forward")
        self.assertEqual(content["body_format"], "html")

    def test_requested_format_wins(self):
        self._set_preferences(editor="html", displaymode="html")
        content = self._content(PLAIN_MESSAGE, "reply", "plain")
        self.assertEqual(content["body_format"], "plain")

    def test_plain_reply_is_not_escaped(self):
        content = self._content(PLAIN_MESSAGE, "reply", "plain")
        self.assertEqual(
            content["body"],
            f'{ATTRIBUTION}\n> L\'equipe <dev> & "co"\n> Second line',
        )
        self.assertEqual(content["body_format"], "plain")

    def test_plain_forward_is_not_escaped(self):
        content = self._content(PLAIN_MESSAGE, "forward", "plain")
        self.assertTrue(content["body"].endswith('L\'equipe <dev> & "co"\nSecond line'))
        self.assertNotIn("<pre>", content["body"])

    def test_html_reply_to_plain_message_is_escaped(self):
        content = self._content(PLAIN_MESSAGE, "reply", "html")
        self.assertIn(
            "L&#x27;equipe &lt;dev&gt; &amp; &quot;co&quot;<br>", content["body"]
        )
        self.assertNotIn("<dev>", content["body"])
        self.assertEqual(content["body_format"], "html")

    def test_plain_reply_to_html_message(self):
        """Without text part, the reply quotes the text of the HTML one."""
        content = self._content(HTML_MESSAGE, "reply", "plain")
        self.assertEqual(
            content["body"],
            f"{ATTRIBUTION}\n> Hello world & co <https://example.test/doc>\n>\n> Bye",
        )
        self.assertEqual(content["body_format"], "plain")

    def test_html_reply_is_a_blockquote(self):
        content = self._content(HTML_MESSAGE, "reply", "html")
        self.assertTrue(
            content["body"].startswith(f'<p>{ATTRIBUTION}</p><blockquote type="cite">')
        )
        self.assertTrue(content["body"].endswith("</blockquote>"))
        # Links are only blocked to protect the reader
        self.assertIn('href="https://example.test/doc"', content["body"])

    def test_html_reply_to_plain_message(self):
        content = self._content(PLAIN_MESSAGE, "reply", "html")
        self.assertIn(
            '<blockquote type="cite">L&#x27;equipe &lt;dev&gt;', content["body"]
        )

    def test_quoted_lines_get_one_more_level(self):
        modifier = ReplyModifier.__new__(ReplyModifier)
        # ImapEmail.__del__ closes a connection: there is none here
        modifier.imapc = mock.MagicMock()
        modifier.dformat = modifier.mformat = "plain"
        modifier.body = "Answer\n\n> Question\n>> Older"
        modifier._modify_plain()
        self.assertEqual(modifier.body, "> Answer\n>\n>> Question\n>>> Older")

    def test_forward_header(self):
        content = self._content(PLAIN_MESSAGE, "forward", "plain")
        self.assertTrue(content["body"].startswith("----- Original message -----\n"))
        self.assertIn("Date: Sept. 15, 2026, 8 a.m.\n", content["body"])
        self.assertEqual(content["subject"], "Fwd: Question")

    def test_embedded_images_only_in_html(self):
        """Images are shown in the HTML editor, useless in plain text."""
        modifier = ReplyModifier.__new__(ReplyModifier)
        modifier.imapc = mock.MagicMock()
        modifier.dformat = "html"
        self.assertTrue(modifier.embed_inlines)
        modifier.dformat = "plain"
        self.assertFalse(modifier.embed_inlines)

    def test_reply_subject_prefixes(self):
        modifier = ReplyModifier.__new__(ReplyModifier)
        modifier.imapc = mock.MagicMock()
        for subject, expected in (
            ("Question", "Re: Question"),
            ("Re: Question", "Re: Question"),
            ("RE : Question", "RE : Question"),
            ("AW: Frage", "AW: Frage"),
            ("Re[2]: Question", "Re[2]: Question"),
            ("Réf. : Dossier", "Réf. : Dossier"),
            ("Fwd: Question", "Re: Fwd: Question"),
            ("Return policy", "Re: Return policy"),
            ("", ""),
        ):
            with self.subTest(subject=subject):
                modifier.Subject = subject
                self.assertEqual(modifier.subject, expected)

    def test_forward_subject_prefixes(self):
        modifier = ForwardModifier.__new__(ForwardModifier)
        modifier.imapc = mock.MagicMock()
        for subject, expected in (
            ("Question", "Fwd: Question"),
            ("Fwd: Question", "Fwd: Question"),
            ("TR: Question", "TR: Question"),
            ("WG: Frage", "WG: Frage"),
            ("Re: Question", "Fwd: Re: Question"),
            ("Travaux", "Fwd: Travaux"),
        ):
            with self.subTest(subject=subject):
                modifier.Subject = subject
                self.assertEqual(modifier.subject, expected)
