"""Sievefilters tests."""

from unittest import mock

from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase

from . import mocks


class SieveFiltersTestCase(ModoTestCase):
    """Check sieve filters."""

    @classmethod
    def setUpTestData(cls):
        """Create some users."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.user = core_models.User.objects.get(username="user@test.com")

    def setUp(self):
        """Connect with a simpler user."""
        patcher = mock.patch("sievelib.managesieve.Client")
        self.mock_client = patcher.start()
        self.mock_client.return_value = mocks.ManagesieveClientMock()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("imaplib.IMAP4")
        self.mock_imap4 = patcher.start()
        self.mock_imap4.return_value = mocks.IMAP4Mock()
        self.addCleanup(patcher.stop)

        url = reverse("core:login")
        data = {"username": self.user.username, "password": "toto"}
        self.client.post(url, data)

    def test_index(self):
        """Test index view."""
        response = self.client.get(reverse("sievefilters:index"))
        self.assertContains(response, "main_script (active)")
        response = self.client.post(reverse("core:logout"))
        self.assertEqual(response.status_code, 302)

    def test_getfs(self):
        """Test getfs view."""
        response = self.ajax_get(reverse("sievefilters:fs_get", args=["main_script"]))
        self.assertIn("/sfilters/main_script/editfilter/test1/", response["content"])

    def test_toggle_filter_state(self):
        """Test toggle_filter_state view."""
        url = reverse("sievefilters:filter_toggle_state", args=["main_script", "test1"])
        response = self.ajax_get(url)
        self.assertEqual(response["color"], "red")
        response = self.ajax_get(url)
        self.assertEqual(response["color"], "green")

    def test_move_filter_up(self):
        """Test move_filter_up view."""
        url = reverse("sievefilters:filter_move_up", args=["main_script", "test2"])
        response = self.ajax_get(url)
        pos1 = response["content"].find("/sfilters/main_script/editfilter/test2/")
        pos2 = response["content"].find("/sfilters/main_script/editfilter/test1/")
        self.assertTrue(pos1 < pos2)

    def test_move_filter_down(self):
        """Test move_filter_down view."""
        url = reverse("sievefilters:filter_move_down", args=["main_script", "test1"])
        response = self.ajax_get(url)
        pos1 = response["content"].find("/sfilters/main_script/editfilter/test2/")
        pos2 = response["content"].find("/sfilters/main_script/editfilter/test1/")
        self.assertTrue(pos1 < pos2)

    def test_new_filter(self):
        """Test new_filter view."""
        url = reverse("sievefilters:filter_add", args=["main_script"])
        response = self.client.get(url)
        self.assertContains(response, "New filter")

        data = {
            "name": "tést filter",
            "match_type": "anyof",
            "conds": 1,
            "cond_target_0": "Subject",
            "cond_operator_0": "contains",
            "cond_value_0": "Test",
            "actions": 1,
            "action_name_0": "fileinto",
            "action_arg_0_0": "Trash",
        }
        response = self.ajax_post(url, data)
        self.assertEqual(response, "Filter created")

    def test_edit_filter(self):
        """Test edit_filter view."""
        url = reverse("sievefilters:filter_change", args=["main_script", "test1"])
        response = self.client.get(url)
        self.assertContains(response, "Edit filter")

        data = {
            "oldname": "test1",
            "name": "test1",
            "match_type": "all",
            "conds": 1,
            "cond_target_0": "To",
            "cond_operator_0": "contains",
            "cond_value_0": "test1",
            "actions": 1,
            "action_name_0": "fileinto",
            "action_arg_0_0": "Trash",
            "action_arg_0_1": True,
        }
        response = self.ajax_post(url, data)
        self.assertEqual(response, "Filter modified")

    def test_edit_filter_with_not(self):
        """Try to edit a filter containing a not operator."""
        url = reverse("sievefilters:filter_change", args=["third_script", "Tést"])
        response = self.client.get(url)
        self.assertContains(response, "Edit filter")

    def test_remove_filter(self):
        """Test removefilter view."""
        url = reverse("sievefilters:filter_delete", args=["second_script", "test1"])
        response = self.ajax_get(url)
        self.assertEqual(response, "Filter removed")

    def test_download_filters_set(self):
        """Test download_filters_set view."""
        url = reverse("sievefilters:fs_download", args=["main_script"])
        response = self.client.get(url)
        self.assertEqual(response.content.decode(), mocks.SAMPLE_SIEVE_SCRIPT)

    def test_activate_filters_set(self):
        """Test activate_filters_set view."""
        url = reverse("sievefilters:fs_activate", args=["second_script"])
        response = self.ajax_get(url)
        self.assertEqual(response["respmsg"], "Filters set activated")

    def test_remove_filters_set(self):
        """Test remove_filters_set view."""
        url = reverse("sievefilters:fs_delete", args=["second_script"])
        response = self.ajax_get(url)
        self.assertEqual(response["respmsg"], "Filters set deleted")

    def test_new_filters_set(self):
        """Test new_filters_set view."""
        url = reverse("sievefilters:fs_add")
        response = self.client.get(url)
        self.assertContains(response, "Create a new filters set")

        data = {"name": "new_script"}
        response = self.ajax_post(url, data)
        self.assertEqual(response["respmsg"], "Filters set created")

    def test_savefs(self):
        """Test savefs view."""
        url = reverse("sievefilters:fs_save", args=["new_script"])
        data = {"scriptcontent": mocks.SAMPLE_SIEVE_SCRIPT}
        response = self.ajax_post(url, data)
        self.assertEqual(response["respmsg"], "Filters set saved")
