"""API v2 tests."""

from unittest import mock

from django.urls import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.sievefilters import mocks


class FilterSetViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):
        """Create some users."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")

    def setUp(self):
        """Connect with a simpler user."""
        super().setUp()
        patcher = mock.patch("sievelib.managesieve.Client")
        self.mock_client = patcher.start()
        self.mock_client.return_value = mocks.ManagesieveClientMock()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("imaplib.IMAP4")
        self.mock_imap4 = patcher.start()
        self.mock_imap4.return_value = mocks.IMAP4Mock()
        self.addCleanup(patcher.stop)

    def authenticate(self, username: str = "user@test.com"):
        # FIXME: replace ASAP with an oauth2 token
        token = Token.objects.create(
            user=core_models.User.objects.get(username=username)
        )
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_list(self):
        self.authenticate()
        url = reverse("v2:filterset-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_create(self):
        self.authenticate()
        url = reverse("v2:filterset-list")
        data = {"name": "Test script", "active": True}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_update(self):
        self.authenticate()
        url = reverse("v2:filterset-detail", args=["unknown"])
        data = {"content": "# Empty script"}
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 404)

        url = reverse("v2:filterset-detail", args=["main_script"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_activate(self):
        self.authenticate()
        url = reverse("v2:filterset-activate", args=["unknown"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

        url = reverse("v2:filterset-activate", args=["main_script"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

    def test_download(self):
        self.authenticate()
        url = reverse("v2:filterset-download", args=["unknown"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        url = reverse("v2:filterset-download", args=["main_script"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_delete(self):
        self.authenticate()
        url = reverse("v2:filterset-detail", args=["unknown"])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)

        url = reverse("v2:filterset-detail", args=["main_script"])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

    def test_retrieve_condition_templates(self):
        self.authenticate()
        url = reverse("v2:filterset-condition-templates")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 5)

    def test_retrieve_action_templates(self):
        self.authenticate()
        url = reverse("v2:filterset-action-templates")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        actions = resp.json()
        self.assertEqual(len(actions), 4)
        self.assertIn("choices", actions[0]["args"][0])
