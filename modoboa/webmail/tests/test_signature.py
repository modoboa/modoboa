"""Tests for the signature added to the messages written."""

from django.test import SimpleTestCase
from django.urls import reverse

from modoboa.webmail.lib import signature, utils
from modoboa.webmail.tests.test_viewsets import WebmailTestCase


class SignatureTestCase(WebmailTestCase):

    def setUp(self):
        super().setUp()
        self.user.parameters.set_value("signature", "<p>John <b>Doe</b></p>")
        self.user.save()

    def _set_editor(self, value):
        self.user.parameters.set_value("editor", value)
        self.user.save()

    def test_plain_signature(self):
        self._set_editor("plain")
        self.assertEqual(str(signature.EmailSignature(self.user)), "-- \nJohn Doe")

    def test_html_signature(self):
        self._set_editor("html")
        self.assertEqual(
            str(signature.EmailSignature(self.user)),
            "<p>-- </p><p>John <b>Doe</b></p>",
        )

    def test_compose_session(self):
        self.authenticate()
        response = self.client.post(reverse("v2:webmail-compose-session-list"))
        self.assertEqual(response.status_code, 201)
        # Above the quoted message unless the user decides otherwise
        self.assertEqual(response.json()["signature_position"], "above")
        self.user.parameters.set_value("signature_position", "below")
        self.user.save()
        response = self.client.post(reverse("v2:webmail-compose-session-list"))
        self.assertEqual(response.json()["signature_position"], "below")


class SignatureSeparatorTestCase(SimpleTestCase):

    def test_separator_keeps_its_space(self):
        """Clients recognize signatures by the "-- " line."""
        self.assertEqual(
            utils.html2plaintext("<p>Hi</p><p>-- </p><p>John</p>"),
            "Hi\n\n-- \n\nJohn",
        )
        self.assertEqual(utils.html2plaintext("<p>--<br>John</p>"), "-- \nJohn")
