"""API v2 tests."""

from unittest import mock
from datetime import timedelta

from sievelib.factory import FiltersSet
from sievelib.parser import Parser

from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import get_access_token_model, get_application_model

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase
from modoboa.sievefilters import mocks
from modoboa.sievefilters.api.v2.serializers import FilterSerializer
from modoboa.webmail.mocks import IMAP4Mock

Application = get_application_model()
AccessToken = get_access_token_model()


class PatcherMixin:
    """Mixin to patch external dependencies."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch("sievelib.managesieve.Client")
        self.mock_client = patcher.start()
        self.mock_client.return_value = mocks.ManagesieveClientMock()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("imaplib.IMAP4")
        self.mock_imap4 = patcher.start()
        self.mock_imap4.return_value = IMAP4Mock()
        self.addCleanup(patcher.stop)


class FilterSetViewSetTestCase(PatcherMixin, ModoAPITestCase):
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

    def test_create_existing_name(self):
        self.authenticate()
        url = reverse("v2:filterset-list")
        for name in ("main_script", "second_script"):
            resp = self.client.post(url, {"name": name}, format="json")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("name", resp.json())
        sclient = self.mock_client.return_value
        self.assertEqual(sclient.scripts["main_script"], mocks.SAMPLE_SIEVE_SCRIPT)

    def test_create_forbidden_characters(self):
        """Check that ManageSieve protocol injection is rejected."""
        self.authenticate()
        url = reverse("v2:filterset-list")
        for name in ['evil"script', "evil\\script", "evil\r\nPUTSCRIPT"]:
            data = {"name": name, "active": False}
            resp = self.client.post(url, data, format="json")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("name", resp.json())

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

    def test_deactivate_active(self):
        self.authenticate()
        url = reverse("v2:filterset-deactivate-active")
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

    def test_retrieve_action_templates_with_subfolders(self):
        # Listing sub-folders needs the hierarchy delimiter
        imap = self.mock_imap4.return_value
        simple_command = imap._simple_command

        def _simple_command(name, *args, **kwargs):
            if name == "LIST":
                imap.untagged_responses["LIST"] = (
                    [b'() "/" "Test/Sub"']
                    if "Test/%" in str(args)
                    else [b'(\\HasChildren) "/" "Test"']
                )
                return "OK", None
            return simple_command(name, *args, **kwargs)

        imap._simple_command = _simple_command
        self.authenticate()
        resp = self.client.get(reverse("v2:filterset-action-templates"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json()[0]["args"][0]["choices"][-2:],
            [
                {"name": "Test", "label": "Test"},
                {"name": "Test/Sub", "label": "Sub"},
            ],
        )

    def test_get_filters(self):
        self.authenticate()
        url = reverse("v2:filterset-get-filters", args=["unknown"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-get-filters", args=["main_script"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 6)
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

    def test_get_filters_unsupported(self):
        self.authenticate()
        scripts = self.mock_client.return_value.scripts
        bodies = [
            'if anyof (header :contains ["From", "To"] "x") { stop; }',
            'if anyof (address :is "From" "x@y.com") { stop; }',
            'if anyof (header :matches "From" "x*") { stop; }',
            'if anyof (header :contains "From" "x") { discard; }',
            "if {",
        ]
        for body in bodies:
            scripts["custom"] = f"# Filter: custom\n{body}\n"
            url = reverse("v2:filterset-get-filters", args=["custom"])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 518, body)

    def test_get_filters_single_test(self):
        self.authenticate()
        self.mock_client.return_value.scripts["custom"] = (
            '# Filter: custom\nif header :is "From" "x" { stop; }\n'
        )
        url = reverse("v2:filterset-get-filters", args=["custom"])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["match_type"], "anyof")

    def test_add_filter_invalid(self):
        self.authenticate()
        url = reverse("v2:filterset-get-filters", args=["main_script"])
        data = {
            "name": "New filter",
            "match_type": "anyof",
            "conditions": [{"name": "From", "operator": "is", "value": "x"}],
            "actions": [{"name": "stop", "args": {}}],
        }
        for key, value in (
            ("name", 'with "quote'),
            ("name", "autoreply"),
            ("actions", [{"name": "unknown", "args": {}}]),
            ("conditions", [{"name": "From", "operator": "unknown", "value": "x"}]),
        ):
            resp = self.client.post(url, {**data, key: value}, format="json")
            self.assertEqual(resp.status_code, 400, value)
            self.assertIn(key, resp.json())

    def test_add_filter_negated_operator(self):
        self.authenticate()
        url = reverse("v2:filterset-get-filters", args=["main_script"])
        data = {
            "name": "New filter",
            "match_type": "anyof",
            "conditions": [{"name": "From", "operator": "notis", "value": "x"}],
            "actions": [{"name": "stop", "args": {}}],
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get(url)
        self.assertEqual(resp.json()[-1]["conditions"], data["conditions"])

    def test_add_filter_unparsable_script(self):
        self.authenticate()
        self.mock_client.return_value.scripts["custom"] = "if {\n"
        url = reverse("v2:filterset-get-filters", args=["custom"])
        data = {
            "name": "New filter",
            "match_type": "anyof",
            "conditions": [{"name": "From", "operator": "is", "value": "x"}],
            "actions": [{"name": "stop", "args": {}}],
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_update_filter_errors(self):
        self.authenticate()
        data = {
            "name": "test2",
            "match_type": "anyof",
            "conditions": [{"name": "From", "operator": "is", "value": "x"}],
            "actions": [{"name": "stop", "args": {}}],
        }
        url = reverse("v2:filterset-update-filter", args=["main_script", "test1"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("name", resp.json())
        url = reverse("v2:filterset-update-filter", args=["main_script", "unknown"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_list_error(self):
        self.authenticate()
        with mock.patch.object(
            self.mock_client.return_value, "listscripts", return_value=None
        ):
            resp = self.client.get(reverse("v2:filterset-list"))
        self.assertEqual(resp.status_code, 400)
        # Empty errmsg is replaced by a generic message
        self.assertTrue(resp.json()["error"])

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
        sclient = self.mock_client.return_value
        enable_url = reverse(
            "v2:filterset-enable-filter", args=["main_script", "test2"]
        )
        disable_url = reverse(
            "v2:filterset-disable-filter", args=["main_script", "test2"]
        )
        # Already enabled: nothing to do
        with mock.patch.object(sclient, "putscript") as putscript:
            resp = self.client.post(enable_url)
        self.assertEqual(resp.status_code, 204)
        putscript.assert_not_called()
        resp = self.client.post(disable_url)
        self.assertEqual(resp.status_code, 204)
        # Already disabled: nothing to do
        with mock.patch.object(sclient, "putscript") as putscript:
            resp = self.client.post(disable_url)
        self.assertEqual(resp.status_code, 204)
        putscript.assert_not_called()
        resp = self.client.post(enable_url)
        self.assertEqual(resp.status_code, 204)
        self.assertIn("# Filter: test2\nif anyof", sclient.scripts["main_script"])

    def test_move_filter(self):
        self.authenticate()
        sclient = self.mock_client.return_value
        url = reverse("v2:filterset-move-filter-up", args=["main_script", "unknown"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        # First filter can't go up
        url = reverse("v2:filterset-move-filter-up", args=["main_script", "test1"])
        with mock.patch.object(sclient, "putscript") as putscript:
            resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
        putscript.assert_not_called()
        url = reverse("v2:filterset-move-filter-down", args=["main_script", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
        script = sclient.scripts["main_script"]
        self.assertLess(script.index("Filter: test2"), script.index("Filter: test1"))

    def test_sieve_client_logout(self):
        self.authenticate()
        sclient = self.mock_client.return_value
        with mock.patch.object(sclient, "logout") as logout:
            self.client.get(reverse("v2:filterset-list"))
            logout.assert_called_once()
            logout.reset_mock()
            url = reverse("v2:filterset-get-filters", args=["unknown"])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 404)
            logout.assert_called_once()

    def test_pushscript_size_in_bytes(self):
        self.authenticate()
        sclient = self.mock_client.return_value
        url = reverse("v2:filterset-detail", args=["main_script"])
        with mock.patch.object(sclient, "havespace", return_value=True) as havespace:
            resp = self.client.put(url, {"content": "# é\nkeep;"}, format="json")
        self.assertEqual(resp.status_code, 200)
        havespace.assert_called_once_with("main_script", len(b"# \xc3\xa9\r\nkeep;"))

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

    def test_filter_with_email_name(self):
        """Test filter operations when the filter name is an email address."""
        self.authenticate()
        email_filter = "user@example.com"
        data = {
            "name": email_filter,
            "enabled": True,
            "match_type": "anyof",
            "conditions": [
                {"name": "From", "operator": "is", "value": email_filter},
            ],
            "actions": [
                {"name": "fileinto", "args": {"mailbox": "Hotels"}},
            ],
        }
        # Update
        url = reverse("v2:filterset-update-filter", args=["main_script", email_filter])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        # Disable
        url = reverse("v2:filterset-disable-filter", args=["main_script", email_filter])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

        # Enable
        url = reverse("v2:filterset-enable-filter", args=["main_script", email_filter])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

        # Move up
        url = reverse("v2:filterset-move-filter-up", args=["main_script", email_filter])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

        # Move down
        url = reverse(
            "v2:filterset-move-filter-down", args=["main_script", email_filter]
        )
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

        # Delete
        url = reverse("v2:filterset-update-filter", args=["main_script", email_filter])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

    def test_move_filter_down(self):
        self.authenticate()
        url = reverse("v2:filterset-move-filter-down", args=["unknown", "test1"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        url = reverse("v2:filterset-move-filter-down", args=["main_script", "test2"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)


class FilterSerializerTestCase(SimpleTestCase):
    def test_quoted_values_round_trip(self):
        """Values containing quotes must not gain backslashes on each save."""
        data = {
            "name": "test",
            "match_type": "anyof",
            "conditions": [{"name": "Subject", "operator": "contains", "value": 'a"b'}],
            "actions": [{"name": "fileinto", "args": {"mailbox": 'Fold"er'}}],
        }
        for _ in range(2):
            serializer = FilterSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            match_type, conditions, actions = serializer.to_filter()
            fset = FiltersSet("test")
            fset.addfilter(data["name"], conditions, actions, match_type)
            parser = Parser()
            self.assertTrue(parser.parse(str(fset)))
            fset = FiltersSet("test")
            fset.from_parser_result(parser)
            data = FilterSerializer.from_filters(fset.filters).data[0]
            self.assertEqual(data["conditions"][0]["value"], 'a"b')
            self.assertEqual(data["actions"][0]["args"]["mailbox"], 'Fold"er')
