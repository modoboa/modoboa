"""Tests for the conversation (threaded) listing."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import imaputils
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class NoThreadIMAP4Mock(IMAP4Mock):
    """A server without the THREAD extension."""

    capabilities = (b"QUOTA", b"SORT")

    def uid(self, command, *args):
        if command == "THREAD":
            return "NO", [b"THREAD not supported"]
        return super().uid(command, *args)


class ParseThreadResponseTestCase(SimpleTestCase):
    """The THREAD response is turned into a flat list of threads."""

    def test_simple_threads(self):
        self.assertEqual(
            imaputils.parse_thread_response([b"(2)(3)(4)"]),
            [["2"], ["3"], ["4"]],
        )

    def test_nested_thread_is_flattened(self):
        self.assertEqual(
            imaputils.parse_thread_response([b"(2)(3 6 (4 23)(44 7 96))"]),
            [["2"], ["3", "6", "4", "23", "44", "7", "96"]],
        )

    def test_bare_uids_are_threads_of_their_own(self):
        self.assertEqual(
            imaputils.parse_thread_response([b"1 2 3"]), [["1"], ["2"], ["3"]]
        )

    def test_response_keyword_is_ignored(self):
        self.assertEqual(
            imaputils.parse_thread_response([b"THREAD (2)(3)"]), [["2"], ["3"]]
        )

    def test_empty_responses(self):
        for data in (None, [], [b""], [b"()"]):
            self.assertEqual(imaputils.parse_thread_response(data), [])

    def test_unbalanced_parenthesis_are_ignored(self):
        for data in ([b"(2"], [b"(2))"], [b"((2)"]):
            self.assertEqual(imaputils.parse_thread_response(data), [])

    def test_unexpected_token_is_ignored(self):
        self.assertEqual(imaputils.parse_thread_response([b"(2) NOPE"]), [])


class ThreadOrderTestCase(SimpleTestCase):
    """Threads are ranked by their most recent message."""

    def _connector(self, sort_result, thread_result, capabilities=None):
        class Mock(IMAP4Mock):
            def uid(self, command, *args):
                if command == "SORT":
                    return "OK", [sort_result]
                if command == "THREAD":
                    return "OK", [thread_result]
                return super().uid(command, *args)

        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.m = Mock()
        connector.capabilities = capabilities or ["SORT", "THREAD=REFERENCES"]
        connector.criterions = []
        connector.select_mailbox = lambda *args, **kwargs: None
        connector.getquota = lambda *args, **kwargs: None
        return connector

    def test_threads_follow_their_latest_message(self):
        connector = self._connector(b"19 18 17", b"(17 19)(18)")

        total = connector.threads_count(mbox="INBOX")

        self.assertEqual(total, 2)
        # 19 is the most recent message, so its thread comes first, and
        # UIDs keep the order of the conversation inside a thread
        self.assertEqual(connector.threads, [["17", "19"], ["18"]])

    def test_messages_deleted_meanwhile_are_dropped(self):
        connector = self._connector(b"19 18", b"(17 19)(18)")

        connector.threads_count(mbox="INBOX")

        self.assertEqual(connector.threads, [["19"], ["18"]])

    def test_without_the_extension_every_message_is_a_thread(self):
        connector = self._connector(b"19 18", b"(19 18)", capabilities=["SORT"])

        total = connector.threads_count(mbox="INBOX")

        self.assertEqual(total, 2)
        self.assertEqual(connector.threads, [["19"], ["18"]])


class ThreadListTestCase(WebmailTestCase):
    """The threads endpoints."""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_list_threads(self):
        url = reverse("v2:webmail-email-threads")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["threading_supported"])
        self.assertEqual(response.json()["count"], 1)
        thread = response.json()["results"][0]
        self.assertEqual(thread["root"], "19")
        self.assertEqual(thread["count"], 1)
        self.assertEqual(thread["uids"], ["19"])
        self.assertEqual(thread["latest"]["imapid"], "19")
        self.assertTrue(thread["participants"])

    def test_list_threads_with_a_search(self):
        url = reverse("v2:webmail-email-threads")
        response = self.client.get(f"{url}?mailbox=INBOX&search=hello")
        self.assertEqual(response.status_code, 200)

    def test_list_threads_rejects_an_invalid_page(self):
        url = reverse("v2:webmail-email-threads")
        response = self.client.get(f"{url}?mailbox=INBOX&page=nope")
        self.assertEqual(response.status_code, 400)

    def test_empty_page(self):
        url = reverse("v2:webmail-email-threads")
        response = self.client.get(f"{url}?mailbox=INBOX&page=1000")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])
        self.assertTrue(response.json()["threading_supported"])

    def test_get_a_thread(self):
        url = reverse("v2:webmail-email-thread")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=19")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["threading_supported"])
        self.assertEqual([msg["imapid"] for msg in response.json()["results"]], ["19"])

    def test_get_a_thread_rejects_an_invalid_mailid(self):
        url = reverse("v2:webmail-email-thread")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=19;NOOP")
        self.assertEqual(response.status_code, 400)


class NoThreadSupportTestCase(WebmailTestCase):
    """A server without THREAD doesn't break the listing."""

    def setUp(self):
        super().setUp()
        self.mock_imap4.return_value = NoThreadIMAP4Mock()
        self.authenticate()

    def test_threads_are_reported_as_unsupported(self):
        url = reverse("v2:webmail-email-threads")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["threading_supported"])
        self.assertEqual(response.json()["results"], [])

    def test_thread_is_reported_as_unsupported(self):
        url = reverse("v2:webmail-email-thread")
        response = self.client.get(f"{url}?mailbox=INBOX&mailid=19")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["threading_supported"])
        self.assertEqual(response.json()["results"], [])

    def test_flat_listing_still_works(self):
        url = reverse("v2:webmail-email-list")
        response = self.client.get(f"{url}?mailbox=INBOX")
        self.assertEqual(response.status_code, 200)
