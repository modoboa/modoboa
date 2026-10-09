"""Tests for the recipients of the messages written: names are kept."""

from dateutil.relativedelta import relativedelta

from django.core import mail
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from modoboa.webmail import factories, models
from modoboa.webmail.lib import utils
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class ParseRecipientTestCase(SimpleTestCase):

    def test_valid_recipients(self):
        for value, expected in (
            ("john@example.test", "john@example.test"),
            ("John Doe <john@example.test>", '"John Doe" <john@example.test>'),
            ('"Doe, John" <john@example.test>', '"Doe, John" <john@example.test>'),
            ('"Say \\"hi\\"" <a@example.test>', '"Say \\"hi\\"" <a@example.test>'),
        ):
            with self.subTest(value=value):
                self.assertEqual(utils.parse_recipient(value), expected)

    def test_invalid_recipients(self):
        for value in ("john", "John <john>", "a@example.test, b@example.test", ""):
            with self.subTest(value=value):
                self.assertIsNone(utils.parse_recipient(value))

    def test_split_recipients(self):
        self.assertEqual(
            utils.split_recipients('"Doe, John" <john@example.test>, b@example.test'),
            ['"Doe, John" <john@example.test>', "b@example.test"],
        )
        # Values stored by previous versions
        self.assertEqual(
            utils.split_recipients("a@example.test,b@example.test"),
            ["a@example.test", "b@example.test"],
        )


class RecipientNamesTestCase(WebmailTestCase):

    RECIPIENTS = ['"Doe, John" <john@example.test>', "Jane <jane@example.test>"]

    def setUp(self):
        super().setUp()
        self.authenticate()
        mail.outbox = []

    def _send(self, **extra):
        uid = self.client.post(reverse("v2:webmail-compose-session-list")).json()["uid"]
        url = reverse("v2:webmail-compose-session-send", args=[uid])
        data = {
            "sender": self.user.email,
            "to": self.RECIPIENTS,
            "cc": ["Bob <bob@example.test>"],
            "subject": "test",
            "body": "Test",
            **extra,
        }
        return self.client.post(url, data, format="json")

    def test_names_are_kept(self):
        self.assertEqual(self._send().status_code, 204)
        message = mail.outbox[0].message()
        self.assertEqual(
            message["To"],
            '"Doe, John" <john@example.test>, "Jane" <jane@example.test>',
        )
        self.assertEqual(message["Cc"], '"Bob" <bob@example.test>')

    def test_invalid_recipient(self):
        response = self._send(to=["John <john>"])
        self.assertEqual(response.status_code, 400)
        self.assertIn("to", response.json())
        self.assertEqual(len(mail.outbox), 0)

    def test_scheduled_message(self):
        scheduled_datetime = timezone.now() + relativedelta(hours=1)
        response = self._send(scheduled_datetime=scheduled_datetime.isoformat())
        self.assertEqual(response.status_code, 204)
        message = models.ScheduledMessage.objects.get()
        attributes = message.to_dict()
        self.assertEqual(
            attributes["to"],
            ['"Doe, John" <john@example.test>', '"Jane" <jane@example.test>'],
        )
        self.assertEqual(attributes["cc"], ['"Bob" <bob@example.test>'])

    def test_message_scheduled_by_previous_versions(self):
        message = factories.ScheduledMessageFactory(
            account=self.user,
            sender=self.user.email,
            scheduled_datetime=timezone.now(),
            to="a@example.test,b@example.test",
        )
        self.assertEqual(message.to_dict()["to"], ["a@example.test", "b@example.test"])
