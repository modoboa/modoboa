"""Tests for the message format: the one chosen in the editor wins."""

from unittest import mock

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import models
from modoboa.webmail.tests.test_viewsets import WebmailTestCase

PUSH_MAIL = "modoboa.webmail.lib.imaputils.IMAPconnector.push_mail"


def has_html_part(message) -> bool:
    return any(
        alternative[1] == "text/html"
        for alternative in getattr(message, "alternatives", [])
    )


class BodyFormatTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _set_editor_preference(self, value):
        self.user.parameters.set_value("editor", value)
        self.user.save()

    def _data(self, **extra):
        return {
            "sender": self.user.email,
            "to": ["test@example.test"],
            "subject": "test",
            "body": "<p>Hello</p>",
            **extra,
        }

    def _session(self):
        return self.client.post(reverse("v2:webmail-compose-session-list")).json()[
            "uid"
        ]

    def _send(self, **extra):
        url = reverse("v2:webmail-compose-session-send", args=[self._session()])
        return self.client.post(url, self._data(**extra), format="json")

    def test_html_chosen_with_plain_preference(self):
        self._set_editor_preference("plain")
        response = self._send(body_format="html")
        self.assertEqual(response.status_code, 204)
        self.assertTrue(has_html_part(mail.outbox[0]))

    def test_plain_chosen_with_html_preference(self):
        self._set_editor_preference("html")
        response = self._send(body_format="plain")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(has_html_part(mail.outbox[0]))
        self.assertEqual(mail.outbox[0].body, "<p>Hello</p>")

    def test_preference_applies_without_format(self):
        """Clients not sending the format keep the previous behaviour."""
        self._set_editor_preference("html")
        self.assertEqual(self._send().status_code, 204)
        self.assertTrue(has_html_part(mail.outbox[0]))

    def test_invalid_format_is_rejected(self):
        response = self._send(body_format="markdown")
        self.assertEqual(response.status_code, 400)
        self.assertIn("body_format", response.json())
        self.assertEqual(len(mail.outbox), 0)

    def test_scheduled_message_keeps_the_chosen_format(self):
        self._set_editor_preference("plain")
        scheduled_datetime = timezone.now() + relativedelta(hours=1)
        response = self._send(
            body_format="html", scheduled_datetime=scheduled_datetime.isoformat()
        )
        self.assertEqual(response.status_code, 204)
        message = models.ScheduledMessage.objects.get()
        self.assertEqual(message.body_format, "html")
        # Rebuilt later by the sending job: still HTML
        self.assertTrue(has_html_part(message.to_email_message()))

    def test_draft_keeps_the_chosen_format(self):
        self._set_editor_preference("plain")
        url = reverse("v2:webmail-compose-session-save", args=[self._session()])
        with mock.patch(PUSH_MAIL, return_value=12) as push_mail:
            response = self.client.post(
                url, self._data(body_format="html"), format="json"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            push_mail.call_args.args[1].get_content_type(), "multipart/alternative"
        )
