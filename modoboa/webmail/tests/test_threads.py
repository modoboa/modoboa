"""Tests for the conversation (threaded) listing."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.core import models as core_models
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
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.commands = []

            def uid(self, command, *args):
                self.commands.append((command, args))
                if command == "SORT":
                    return "OK", [sort_result]
                if command == "THREAD":
                    return "OK", [thread_result]
                return super().uid(command, *args)

        connector = imaputils.IMAPconnector.__new__(imaputils.IMAPconnector)
        connector.m = Mock()
        connector.capabilities = capabilities or ["SORT", "THREAD=REFS"]
        connector.criterions = []
        connector.select_mailbox = lambda *args, **kwargs: None
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

    def _thread_argument(self, connector) -> bytes:
        args = next(args for name, args in connector.m.commands if name == "THREAD")
        return args[0]

    def test_refs_is_preferred_over_references(self):
        """REFERENCES also merges threads sharing a base subject.

        That last step of RFC 5256 puts unrelated messages in the same
        conversation; REFS is the same algorithm without it, and matches
        what mail clients display.
        """
        connector = self._connector(
            b"19", b"(19)", capabilities=["THREAD=REFERENCES", "THREAD=REFS"]
        )

        connector.threads_count(mbox="INBOX")

        self.assertEqual(connector.thread_algorithm, "REFS")
        self.assertEqual(self._thread_argument(connector), b"REFS")

    def test_references_is_used_when_refs_is_missing(self):
        connector = self._connector(b"19", b"(19)", capabilities=["THREAD=REFERENCES"])

        connector.threads_count(mbox="INBOX")

        self.assertEqual(connector.thread_algorithm, "REFERENCES")
        self.assertEqual(self._thread_argument(connector), b"REFERENCES")

    def test_no_algorithm_without_the_extension(self):
        connector = self._connector(b"19", b"(19)", capabilities=["SORT"])

        self.assertIsNone(connector.thread_algorithm)
        self.assertFalse(connector.has_thread)


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


class ListingModePreferenceTestCase(WebmailTestCase):
    """The listing mode is a user preference."""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def _parameters(self) -> dict:
        user = core_models.User.objects.get(pk=self.user.pk)
        return user.parameters

    def _listing_mode(self) -> str:
        return self._parameters().get_value("listing_mode")

    def _current_values(self, url) -> dict:
        """The preferences, as the interface sends them back on save.

        Unset values are returned as null but refused on save, so they
        are dropped, the way an empty form field would be.
        """
        params = self.client.get(url).json()["params"]
        return {key: value for key, value in params.items() if value is not None}

    def test_default_is_the_flat_listing(self):
        self.assertEqual(self._listing_mode(), "flat")

    def test_switch_to_conversations(self):
        url = reverse("v2:parameter-user-detail", args=["webmail"])
        data = self._current_values(url)
        data["listing_mode"] = "threaded"
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._listing_mode(), "threaded")
        # The other preferences are left alone
        self.assertEqual(
            self._parameters().get_value("messages_per_page"),
            data["messages_per_page"],
        )

    def test_unknown_mode_is_rejected(self):
        url = reverse("v2:parameter-user-detail", args=["webmail"])
        data = self._current_values(url)
        data["listing_mode"] = "nonsense"
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 400)
