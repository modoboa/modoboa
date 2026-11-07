"""Tests for message tags (IMAP keywords)."""

from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail import constants, models
from modoboa.webmail.exceptions import InvalidImapArgument
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.serializers import generate_keyword
from modoboa.webmail.lib.imaputils import (
    IMAPconnector,
    validate_imap_keyword,
    validate_imap_partnum,
    validate_imap_uid,
)
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

ADD_FLAG = "modoboa.webmail.lib.imaputils.IMAPconnector._add_flag"
REMOVE_FLAG = "modoboa.webmail.lib.imaputils.IMAPconnector._remove_flag"


class GenerateKeywordTestCase(SimpleTestCase):
    def test_label_is_slugified(self):
        self.assertEqual(generate_keyword("To review", set()), "to-review")

    def test_fallback_to_label_number(self):
        # Nothing left once slugified, taken or reserved
        self.assertEqual(generate_keyword("日本", set()), "$label1")
        self.assertEqual(generate_keyword("Junk", set()), "$label1")
        self.assertEqual(
            generate_keyword("work", {"work", "$label1", "$label2"}), "$label3"
        )


class KeywordCommandsTestCase(SimpleTestCase):
    def test_keyword_is_validated(self):
        imapc = IMAPconnector.__new__(IMAPconnector)
        imapc._add_flag = mock.Mock()
        imapc.add_keyword("INBOX", ["1"], "$label1")
        imapc._add_flag.assert_called_once_with("INBOX", ["1"], "($label1)")
        for value in ["\\Deleted", "a b", "x)\r\nA1 LOGOUT", ""]:
            with self.assertRaises(InvalidImapArgument):
                imapc.add_keyword("INBOX", ["1"], value)


class TrailingNewlineTestCase(SimpleTestCase):
    def test_trailing_newline_is_rejected(self):
        """A "$" anchor would let a final newline reach the IMAP command."""
        for validate, value in [
            (validate_imap_uid, "12"),
            (validate_imap_partnum, "1.2"),
            (validate_imap_keyword, "$label1"),
        ]:
            self.assertEqual(validate(value), value)
            with self.assertRaises(InvalidImapArgument):
                validate(f"{value}\n")


class TagViewSetTestCase(WebmailTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_defaults_created_once(self):
        url = reverse("v2:webmail-tag-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [tag["keyword"] for tag in response.json()],
            [tag[0] for tag in constants.DEFAULT_TAGS],
        )
        self.client.get(url)
        self.assertEqual(
            models.Tag.objects.filter(account=self.user).count(),
            len(constants.DEFAULT_TAGS),
        )

    def test_create_update(self):
        url = reverse("v2:webmail-tag-list")
        response = self.client.post(
            url, {"label": "Invoices", "color": "#123456"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        tag = response.json()
        self.assertEqual(tag["keyword"], "invoices")
        # The keyword stays: messages carry it
        response = self.client.patch(
            reverse("v2:webmail-tag-detail", args=[tag["pk"]]),
            {"label": "Bills", "keyword": "other"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["keyword"], "invoices")
        self.assertEqual(response.json()["label"], "Bills")

    def test_invalid_input(self):
        url = reverse("v2:webmail-tag-list")
        self.client.post(url, {"label": "Work", "color": "#123456"}, format="json")
        response = self.client.post(
            url, {"label": "work", "color": "#123456"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("label", response.json())
        response = self.client.post(
            url, {"label": "Other", "color": "red"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("color", response.json())

    def test_max_tags(self):
        models.Tag.objects.bulk_create(
            models.Tag(
                account=self.user, keyword=f"t{i}", label=f"T{i}", color="#000000"
            )
            for i in range(constants.MAX_TAGS_PER_USER)
        )
        response = self.client.post(
            reverse("v2:webmail-tag-list"),
            {"label": "One more", "color": "#123456"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_tags_of_other_users_are_hidden(self):
        other = models.Tag.objects.create(
            account=self.user.__class__.objects.exclude(pk=self.user.pk).first(),
            keyword="secret",
            label="Secret",
            color="#000000",
        )
        response = self.client.delete(reverse("v2:webmail-tag-detail", args=[other.pk]))
        self.assertEqual(response.status_code, 404)


class TagMessagesTestCase(WebmailTestCase):
    def setUp(self):
        super().setUp()
        self.authenticate()
        models.Tag.objects.create(
            account=self.user, keyword="$label1", label="Important", color="#ff0000"
        )

    def _tag(self, **data):
        return self.client.post(
            reverse("v2:webmail-email-tag"),
            {"mailbox": "INBOX", "selection": ["19", "20"], **data},
            format="json",
        )

    def test_add_and_remove(self):
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._tag(tag="$label1", action="add")
        self.assertEqual(response.status_code, 200)
        add_flag.assert_called_once_with("INBOX", ["19", "20"], "($label1)")
        with mock.patch(REMOVE_FLAG) as remove_flag:
            response = self._tag(tag="$label1", action="remove")
        self.assertEqual(response.status_code, 200)
        remove_flag.assert_called_once_with("INBOX", ["19", "20"], "($label1)")

    def test_only_user_tags(self):
        """The endpoint can't be used to set other flags."""
        with mock.patch(ADD_FLAG) as add_flag:
            response = self._tag(tag="\\Deleted", action="add")
        self.assertEqual(response.status_code, 400)
        add_flag.assert_not_called()

    def test_listing_returns_tags(self):
        response = self.client.get(
            reverse("v2:webmail-email-list"), {"mailbox": "INBOX"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["tags"], ["$label1", "todo"])
        response = self.client.get(
            reverse("v2:webmail-email-threads"), {"mailbox": "INBOX"}
        )
        self.assertEqual(response.json()["results"][0]["tags"], ["$label1", "todo"])

    def test_listing_filtered_by_tag(self):
        with mock.patch.object(
            IMAP4Mock, "uid", autospec=True, side_effect=IMAP4Mock.uid
        ) as uid:
            response = self.client.get(
                reverse("v2:webmail-email-list"), {"mailbox": "INBOX", "tag": "$label1"}
            )
        self.assertEqual(response.status_code, 200)
        sort = next(call for call in uid.call_args_list if call.args[1] == "SORT")
        self.assertIn(b"KEYWORD $label1", sort.args)
        response = self.client.get(
            reverse("v2:webmail-email-list"), {"mailbox": "INBOX", "tag": "a b"}
        )
        self.assertEqual(response.status_code, 400)
