"""Tests for the protection of special mailboxes (deletion and renaming)."""

from unittest import mock

from django.urls import reverse

from modoboa.webmail.tests.test_viewsets import WebmailTestCase

DELETE_FOLDER = "modoboa.webmail.lib.imaputils.IMAPconnector.delete_folder"
RENAME_FOLDER = "modoboa.webmail.lib.imaputils.IMAPconnector.rename_folder"

# Default preferences, INBOX in any case and the scheduled messages folder
SPECIAL_NAMES = ["INBOX", "inbox", "Drafts", "Sent", "Junk", "Trash", "Scheduled"]


class SpecialMailboxDeletionTestCase(WebmailTestCase):
    """The webmail relies on special mailboxes: they can't be deleted."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        self.url = reverse("v2:webmail-mailbox-delete")

    def _delete(self, name):
        return self.client.post(self.url, {"name": name}, format="json")

    def test_special_mailboxes_cannot_be_deleted(self):
        for name in SPECIAL_NAMES:
            with self.subTest(name=name), mock.patch(DELETE_FOLDER) as delete_folder:
                response = self._delete(name)
                self.assertEqual(response.status_code, 400)
                self.assertIn("can't be deleted", response.json()["error"])
                delete_folder.assert_not_called()

    def test_user_preferences_are_followed(self):
        self.user.parameters.set_value("trash_folder", "Corbeille")
        self.user.save()
        with mock.patch(DELETE_FOLDER) as delete_folder:
            self.assertEqual(self._delete("Corbeille").status_code, 400)
            delete_folder.assert_not_called()
            # No longer the trash folder: an ordinary one
            self.assertEqual(self._delete("Trash").status_code, 204)
            delete_folder.assert_called_once_with("Trash")

    def test_ordinary_mailbox_can_be_deleted(self):
        with mock.patch(DELETE_FOLDER) as delete_folder:
            self.assertEqual(self._delete("Archives").status_code, 204)
        delete_folder.assert_called_once_with("Archives")


class SpecialMailboxRenamingTestCase(WebmailTestCase):
    """Renaming a special mailbox breaks the features relying on it too."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        self.url = reverse("v2:webmail-mailbox-rename")

    def _rename(self, oldname, **extra):
        data = {"oldname": oldname, "name": "Renamed", **extra}
        return self.client.post(self.url, data, format="json")

    def test_special_mailboxes_cannot_be_renamed(self):
        for name in SPECIAL_NAMES:
            with self.subTest(name=name), mock.patch(RENAME_FOLDER) as rename_folder:
                response = self._rename(name)
                self.assertEqual(response.status_code, 400)
                self.assertIn("can't be renamed", response.json()["error"])
                rename_folder.assert_not_called()

    def test_special_mailbox_cannot_be_moved(self):
        """Moving under another parent is a rename too."""
        with mock.patch(RENAME_FOLDER) as rename_folder:
            response = self._rename("Trash", name="Trash", parent_mailbox="Archives")
        self.assertEqual(response.status_code, 400)
        rename_folder.assert_not_called()

    def test_user_preferences_are_followed(self):
        self.user.parameters.set_value("drafts_folder", "Brouillons")
        self.user.save()
        with mock.patch(RENAME_FOLDER) as rename_folder:
            self.assertEqual(self._rename("Brouillons").status_code, 400)
            rename_folder.assert_not_called()
            # No longer the drafts folder: an ordinary one
            self.assertEqual(self._rename("Drafts").status_code, 200)
            rename_folder.assert_called_once_with("Drafts", "Renamed")

    def test_ordinary_mailbox_can_be_renamed(self):
        with mock.patch(RENAME_FOLDER) as rename_folder:
            self.assertEqual(self._rename("Archives").status_code, 200)
        rename_folder.assert_called_once_with("Archives", "Renamed")
