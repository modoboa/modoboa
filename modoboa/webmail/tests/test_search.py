"""Tests for the messages search."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import imaputils
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class NoSortIMAP4Mock(IMAP4Mock):
    """A server without the SORT extension, answering SEARCH instead."""

    capabilities = (b"QUOTA",)
    search_result = b"19"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = []

    def uid(self, command, *args):
        self.commands.append((command, args))
        if command == "SORT":
            return "NO", [b"SORT not supported"]
        if command == "SEARCH":
            return "OK", [self.search_result]
        return super().uid(command, *args)


class SearchCriteriaTestCase(SimpleTestCase):
    """The pattern is looked for in the headers and in the body."""

    def _connector(self):
        return imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)

    def _criterions(self, criterion, pattern):
        connector = self._connector()
        connector.parse_search_parameters(criterion, pattern)
        return connector.criterions[0].decode()

    def test_default_criteria(self):
        criterions = self._criterions("all", "hello")
        for key in ("FROM", "TO", "CC", "SUBJECT", "BODY"):
            self.assertIn(f'({key} "hello")', criterions)

    def test_both_is_still_sender_and_subject(self):
        self.assertEqual(
            self._criterions("both", "hello"),
            'OR (FROM "hello") (SUBJECT "hello")',
        )

    def test_single_criterion(self):
        self.assertEqual(self._criterions("subject", "hello"), '(SUBJECT "hello")')

    def test_empty_pattern_matches_everything(self):
        self.assertEqual(self._criterions("all", ""), "ALL")

    def test_unknown_criterion_falls_back_to_a_full_search(self):
        self.assertEqual(self._criterions("nonsense", "hello"), '(TEXT "hello")')


class SortFallbackTestCase(WebmailTestCase):
    """A server without SORT still returns a sorted list."""

    def setUp(self):
        super().setUp()
        self.imap = NoSortIMAP4Mock()
        self.mock_imap4.return_value = self.imap
        self.authenticate()

    def test_list_without_sort(self):
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        commands = [name for name, args in self.imap.commands]
        self.assertNotIn("SORT", commands)
        self.assertIn("SEARCH", commands)

    def test_messages_are_ordered_by_arrival(self):
        imap = NoSortIMAP4Mock()
        imap.search_result = b"17 19 18"
        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.m = imap
        connector.capabilities = ["QUOTA"]
        connector.criterions = []
        connector.select_mailbox = lambda *args, **kwargs: None
        connector.getquota = lambda *args, **kwargs: None

        total = connector.messages_count(mbox="INBOX")

        self.assertEqual(total, 3)
        # Most recent first, as the SORT version returns them
        self.assertEqual(connector.messages, ["19", "18", "17"])

    def test_search_is_sent_with_the_criterions(self):
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX&search=hello")
        self.assertEqual(response.status_code, 200)
        search = next(args for name, args in self.imap.commands if name == "SEARCH")
        criterions = bytes(search[-1])
        self.assertIn(b'(SUBJECT "hello")', criterions)
        self.assertIn(b'(BODY "hello")', criterions)
