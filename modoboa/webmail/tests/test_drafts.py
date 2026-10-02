"""Tests for the drafts saved from the webmail."""

from unittest import mock

from django.urls import reverse

from modoboa.webmail.exceptions import ImapError, WebmailInternalError
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

DELETE_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.delete_mail"
PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"


class SaveDraftTestCase(WebmailTestCase):
    """A new version of a draft replaces the previous one only once stored."""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def _save(self):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-save", args=[uid])
        data = {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "subject": "Draft",
            "body": "Test",
            "mailid": 10,
        }
        return self.client.post(url, data, format="json")

    def test_new_version_is_stored_first(self):
        calls = mock.Mock()
        with (
            mock.patch(PUSH_MAIL, return_value=12) as push_mail,
            mock.patch(DELETE_MAIL) as delete_mail,
        ):
            calls.attach_mock(push_mail, "push_mail")
            calls.attach_mock(delete_mail, "delete_mail")
            response = self._save()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mailid"], 12)
        self.assertEqual(
            [call[0] for call in calls.mock_calls], ["push_mail", "delete_mail"]
        )
        delete_mail.assert_called_once_with("Drafts", 10)

    def test_failed_save_keeps_previous_version(self):
        with (
            mock.patch(PUSH_MAIL, side_effect=WebmailInternalError("Quota exceeded")),
            mock.patch(DELETE_MAIL) as delete_mail,
        ):
            response = self._save()
        self.assertEqual(response.status_code, 500)
        delete_mail.assert_not_called()

    def test_leftover_previous_version_is_not_an_error(self):
        with (
            mock.patch(PUSH_MAIL, return_value=12),
            mock.patch(DELETE_MAIL, side_effect=ImapError("No such message")),
            self.assertLogs("modoboa.webmail", level="ERROR"),
        ):
            response = self._save()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mailid"], 12)
