"""Tests for folder sharing (IMAP ACL, RFC 4314)."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.core import models as core_models
from modoboa.webmail import constants
from modoboa.webmail.lib.imaputils import parse_acl_response
from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

# Responses of Dovecot 2.3 with the shared namespace of modoboa-installer
LIST_RESPONSES = {
    "%": [
        b'(\\Subscribed \\HasNoChildren) "/" INBOX',
        b'(\\NonExistent \\HasChildren) "/" shared',
    ],
    "shared/%": [b'(\\NonExistent \\HasChildren) "/" shared/admin@test.com'],
    "shared/admin@test.com/%": [b'(\\HasNoChildren) "/" shared/admin@test.com/Projets'],
    "Projets/*": [b'() "/" Projets/2026', b'() "/" "Projets/Mon dossier"'],
}


class SharingIMAP4Mock(IMAP4Mock):
    capabilities = IMAP4Mock.capabilities + (b"ACL", b"RIGHTS=texk")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.acl_calls = []

    def _simple_command(self, name, *args, **kwargs):
        if name == "NAMESPACE":
            self.untagged_responses["NAMESPACE"] = [b'(("" "/")) (("shared/" "/")) NIL']
            return "OK", None
        if name == "LIST":
            pattern = args[1]
            if isinstance(pattern, bytes):
                pattern = pattern.decode()
            # No untagged response at all when nothing matches
            if pattern.strip('"') in LIST_RESPONSES:
                self.untagged_responses["LIST"] = LIST_RESPONSES[pattern.strip('"')]
            return "OK", None
        return super()._simple_command(name, *args, **kwargs)

    def getacl(self, mailbox):
        return "OK", [b"Projets admin@test.com lrs user@test.com lrwstipekxacd"]

    def myrights(self, mailbox):
        return "OK", [b"shared/admin@test.com/Projets eilprwtsd"]

    def setacl(self, mailbox, identifier, rights):
        self.acl_calls.append(("setacl", mailbox, identifier, rights))
        return "OK", None

    def deleteacl(self, mailbox, identifier):
        self.acl_calls.append(("deleteacl", mailbox, identifier))
        return "OK", None


class SharingLevelTestCase(SimpleTestCase):
    def test_get_sharing_level(self):
        self.assertEqual(constants.get_sharing_level("lrs"), "read")
        # Dovecot sorts the rights and adds the obsolete ones
        self.assertEqual(constants.get_sharing_level("eilprwtsd"), "write")
        self.assertEqual(constants.get_sharing_level("lrswipktexcd"), "manage")
        self.assertEqual(constants.get_sharing_level("lr"), "custom")
        for letters in constants.SHARING_LEVELS.values():
            self.assertNotIn("a", letters)

    def test_parse_acl_response(self):
        self.assertEqual(
            parse_acl_response([b'"Mon \\"dossier\\"" bob@test.com lrs']),
            ['Mon "dossier"', "bob@test.com", "lrs"],
        )


class FolderSharingTestCase(WebmailTestCase):
    def setUp(self):
        super().setUp()
        self.imap = SharingIMAP4Mock()
        self.mock_imap4.return_value = self.imap
        self.authenticate()
        self.acl_url = reverse("v2:webmail-mailbox-acl")

    def test_list(self):
        response = self.client.get(reverse("v2:webmail-mailbox-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["sharing_enabled"])
        shared = response.json()["mailboxes"][-1]
        self.assertEqual(shared["name"], "shared")
        self.assertEqual(shared["type"], "shared")
        self.assertEqual(shared["label"], "Shared with me")
        self.assertFalse(shared["removed"])

    def test_list_owners_and_unsubscribed_folders(self):
        core_models.User.objects.filter(username="admin@test.com").update(
            first_name="Alice", last_name="Martin"
        )
        url = reverse("v2:webmail-mailbox-list")
        response = self.client.get(url, {"mailbox": "shared"})
        owner = response.json()["mailboxes"][0]
        self.assertEqual(owner["label"], "Alice Martin")
        self.assertEqual(owner["owner"], "admin@test.com")
        response = self.client.get(url, {"mailbox": "shared/admin@test.com"})
        folder = response.json()["mailboxes"][0]
        # Listed although nobody subscribes to shared folders
        self.assertEqual(folder["name"], "shared/admin@test.com/Projets")
        self.assertEqual(folder["owner"], "admin@test.com")

    def test_list_nothing_shared_anymore(self):
        response = self.client.get(
            reverse("v2:webmail-mailbox-list"), {"mailbox": "shared/gone@test.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mailboxes"], [])

    def test_sharing_not_available(self):
        self.mock_imap4.return_value = IMAP4Mock()
        response = self.client.get(self.acl_url, {"mailbox": "Projets"})
        self.assertEqual(response.status_code, 400)
        response = self.client.get(reverse("v2:webmail-mailbox-list"))
        self.assertFalse(response.json()["sharing_enabled"])

    def test_get_acl(self):
        response = self.client.get(self.acl_url, {"mailbox": "Projets"})
        self.assertEqual(response.status_code, 200)
        # The owner is left out
        self.assertEqual(
            response.json()["shares"],
            [{"grantee": "admin@test.com", "level": "read", "rights": "lrs"}],
        )

    def test_share(self):
        response = self.client.put(
            self.acl_url,
            {"mailbox": "Projets", "grantee": "admin@test.com", "level": "write"},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            [call[1] for call in self.imap.acl_calls],
            [b'"Projets"', b'"Projets/2026"', b'"Projets/Mon dossier"'],
        )
        self.assertEqual(
            {call[2:] for call in self.imap.acl_calls},
            {("admin@test.com", "lrswipte")},
        )

    def test_share_with_unknown_account(self):
        for grantee in ["user@test2.com", "user@test.com", "anyone"]:
            response = self.client.put(
                self.acl_url,
                {"mailbox": "Projets", "grantee": grantee, "level": "read"},
                format="json",
            )
            self.assertEqual(response.status_code, 400, grantee)
        response = self.client.put(
            self.acl_url,
            {"mailbox": "Projets", "grantee": "admin@test.com", "level": "admin"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.imap.acl_calls, [])

    def test_unshare(self):
        response = self.client.delete(
            self.acl_url,
            {"mailbox": "Projets", "grantee": "someone@other.org"},
            format="json",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(self.imap.acl_calls), 3)
        self.assertEqual(self.imap.acl_calls[0][0], "deleteacl")
        for grantee in ["user@test.com", "bad grantee", 'bad"grantee']:
            response = self.client.delete(
                self.acl_url, {"mailbox": "Projets", "grantee": grantee}, format="json"
            )
            self.assertEqual(response.status_code, 400, grantee)

    def test_rights(self):
        response = self.client.get(
            reverse("v2:webmail-mailbox-rights"),
            {"mailbox": "shared/admin@test.com/Projets"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"rights": "eilprwtsd"})

    def test_share_candidates(self):
        response = self.client.get(reverse("v2:webmail-mailbox-share-candidates"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), [{"address": "admin@test.com", "name": "admin@test.com"}]
        )
