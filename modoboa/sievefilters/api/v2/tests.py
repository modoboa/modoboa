"""API v2 tests."""

from unittest import mock
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import get_access_token_model, get_application_model

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.sievefilters import mocks

Application = get_application_model()
AccessToken = get_access_token_model()


class FilterSetViewSetTestCase(ModoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create some users."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")

        cls.application = Application.objects.create(
            name="Test Application",
            redirect_uris="http://localhost",
            user=cls.user,
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        )

        cls.access_token = AccessToken.objects.create(
            user=cls.user,
            scope="read write",
            expires=timezone.now() + timedelta(seconds=300),
            token="secret-access-token-key",
            application=cls.application,
        )

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
        self.client.credentials(Authorization="Bearer " + self.access_token.token)

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

    def test_get_filters(self):
        self.authenticate()
        url = reverse("v2:filterset-get-filters", args=["unknown"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-get-filters", args=["main_script"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 5)
        url = reverse("v2:filterset-get-filters", args=["complex_script"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 518)

    def test_add_filter(self):
        self.authenticate()
        url = reverse("v2:filterset-get-filters", args=["unknown"])
        data = {
            "name": "New filter",
            "enabled": True,
            "match_type": "anyof",
            "conditions": [
                {"name": "From", "operator": "is", "value": "toto@titi.com"},
            ],
            "actions": [
                {"name": "redirect", "args": {"address": "tata@titi.com"}},
            ],
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-get-filters", args=["main_script"])
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_update_filter(self):
        self.authenticate()
        url = reverse("v2:filterset-update-filter", args=["unknown", "test1"])
        data = {
            "name": "test1",
            "enabled": True,
            "match_type": "anyof",
            "conditions": [
                {"name": "From", "operator": "is", "value": "toto@titi.com"},
            ],
            "actions": [
                {"name": "redirect", "args": {"address": "tata@titi.com"}},
            ],
        }
        resp = self.client.put(url, data)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-update-filter", args=["main_script", "test1"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_disable_filter(self):
        self.authenticate()
        url = reverse("v2:filterset-disable-filter", args=["unknown", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-disable-filter", args=["main_script", "unknown"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-disable-filter", args=["main_script", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

    def test_enable_filter(self):
        self.authenticate()
        url = reverse("v2:filterset-enable-filter", args=["unknown", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-enable-filter", args=["main_script", "unknown"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        # We can't enable a filter which is not disabled
        url = reverse("v2:filterset-enable-filter", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        # So we disable it
        url = reverse("v2:filterset-disable-filter", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
        # And we enable it again
        url = reverse("v2:filterset-enable-filter", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

    def test_delete_filter(self):
        self.authenticate()
        url = reverse("v2:filterset-update-filter", args=["unknown", "test2"])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-update-filter", args=["main_script", "unknown"])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-update-filter", args=["main_script", "test2"])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

    def test_move_filter_up(self):
        self.authenticate()
        url = reverse("v2:filterset-move-filter-up", args=["unknown", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-move-filter-up", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

    def test_move_filter_down(self):
        self.authenticate()
        url = reverse("v2:filterset-move-filter-down", args=["unknown", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-move-filter-down", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
