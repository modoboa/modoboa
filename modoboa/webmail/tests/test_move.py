"""Tests for moving messages between mailboxes."""

from django.urls import reverse

from modoboa.webmail.mocks import IMAP4Mock
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class RecordingMock(IMAP4Mock):
    """Server without MOVE nor UIDPLUS, recording the commands it gets."""

    capability = b"QUOTA"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commands = []
        self.uid_commands = []

    def _simple_command(self, name, *args, **kwargs):
        self.commands.append(name)
        if name == "CAPABILITY":
            self.untagged_responses["CAPABILITY"] = [self.capability]
            return "OK", None
        return super()._simple_command(name, *args, **kwargs)

    def uid(self, command, *args):
        self.uid_commands.append((command, [str(arg) for arg in args]))
        return super().uid(command, *args)

    @property
    def uid_command_names(self):
        return [command for command, _args in self.uid_commands]


class MoveMock(RecordingMock):
    """Server supporting MOVE (RFC 6851)."""

    capability = b"QUOTA MOVE UIDPLUS"


class UidplusMock(RecordingMock):
    """Server supporting UIDPLUS (RFC 4315) but not MOVE."""

    capability = b"QUOTA UIDPLUS"


class MoveMessagesTestCase(WebmailTestCase):
    """Moved messages must not be left behind in the source mailbox."""

    def _move(self, mock):
        self.mock_imap4.return_value = mock
        self.authenticate()
        response = self.client.post(
            reverse("v2:webmail-email-move"),
            {"source": "INBOX", "destination": "Archive", "selection": ["12", "13"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return mock

    def test_move_command_is_used(self):
        mock = self._move(MoveMock())
        self.assertIn("MOVE", mock.uid_command_names)
        self.assertNotIn("COPY", mock.uid_command_names)
        self.assertNotIn("STORE", mock.uid_command_names)
        self.assertNotIn("EXPUNGE", mock.commands)

    def test_uid_expunge_when_move_is_missing(self):
        mock = self._move(UidplusMock())
        self.assertEqual(mock.uid_command_names, ["COPY", "STORE", "EXPUNGE"])
        # Only the moved messages are expunged
        self.assertEqual(mock.uid_commands[-1][1][0], "12,13")
        # Never a mailbox-wide EXPUNGE: it would remove messages another
        # client flagged as deleted.
        self.assertNotIn("EXPUNGE", mock.commands)

    def test_old_server_keeps_previous_behaviour(self):
        mock = self._move(RecordingMock())
        self.assertEqual(mock.uid_command_names, ["COPY", "STORE"])
        self.assertNotIn("EXPUNGE", mock.commands)

    def test_draft_replacement_expunges_by_uid(self):
        """Saving a draft again must not expunge the whole folder."""
        mock = UidplusMock()
        self.mock_imap4.return_value = mock
        self.authenticate()
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        response = self.client.post(
            reverse("v2:webmail-compose-session-save", args=[uid]),
            {
                "sender": self.user.email,
                "to": ["test@example.test"],
                "subject": "test",
                "body": "Test",
                "mailid": 11,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("EXPUNGE", mock.uid_command_names)
        self.assertEqual(mock.uid_commands[-1][1][0], "11")
        self.assertNotIn("EXPUNGE", mock.commands)
