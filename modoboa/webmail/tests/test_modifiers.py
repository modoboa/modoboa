"""Tests for the body of replies and forwards, as loaded into the editor."""

from django.urls import reverse

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
HTML_BODY = b"<p>Hello <b>world</b> &amp; co</p><p>Bye</p>"
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

    def _content(self, mailid, context, dformat):
        url = reverse("v2:webmail-email-content")
        response = self.client.get(
            url,
            {
                "mailbox": "INBOX",
                "mailid": mailid,
                "context": context,
                "dformat": dformat,
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_plain_reply_is_not_escaped(self):
        content = self._content(PLAIN_MESSAGE, "reply", "plain")
        self.assertEqual(
            content["body"],
            '>John Doe wrote:\n>L\'equipe <dev> & "co"\n>Second line',
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
            content["body"], ">John Doe wrote:\n>Hello world & co\n>\n>Bye"
        )
        self.assertEqual(content["body_format"], "plain")
