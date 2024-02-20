"""API v2 tests."""

import shutil
import os

from django.test import override_settings
from django.urls import reverse

from modoboa.admin import factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase


class PDFCredentialViewTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def _create_account(self, username, expected_status=201):
        url = reverse("v2:account-list")
        data = {
            "username": f"{username}",
            "role": "SimpleUsers",
            "mailbox": {"use_domain_quota": True},
            "password": "Toto12345",
            "language": "fr",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, expected_status)
        return data

    def test_pdfcredentials_disabled(self):
        self.set_global_parameter("enabled_pdfcredentials", False)
        values = self._create_account("leon5@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertFalse(os.path.exists(fname))

        # Check that link is not present in listing page
        response = self.client.get(reverse("v2:identities-list"), format="json")
        assert_action_in_response = False
        for res_dict in response.json():
            for action in res_dict["possible_actions"]:
                try:
                    if action.get("icon") == "mdi-file-download-outline":
                        assert_action_in_response = True
                        break
                except KeyError:
                    continue
        self.assertFalse(assert_action_in_response)

    def test_password_updated(self):
        """Check that document is generated at account creation/update."""
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))
        account = core_models.User.objects.get(username=values["username"])

        # Check if link is present in listing page
        response = self.client.get(reverse("v2:identities-list"), format="json")
        assert_action_in_response = False
        for res_dict in response.json():
            for action in res_dict["possible_actions"]:
                try:
                    if action.get("icon") == "mdi-file-download-outline":
                        assert_action_in_response = True
                        break
                except KeyError:
                    continue
        self.assertTrue(assert_action_in_response)

        # Try to download the file
        response = self.client.get(reverse("v2:get-credentials", args=[account.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # File have been deleted?
        self.assertFalse(os.path.exists(fname))

        # Try to download a second time
        response = self.client.get(reverse("v2:get-credentials", args=[account.pk]))
        self.assertEqual(
            response.json()["detail"], "No document available for this user"
        )

        # Update account
        values.update({"language": "en"})
        self.client.patch(
            reverse("v2:account-detail", args=[account.pk]), values, format="json"
        )
        self.assertFalse(os.path.exists(fname))

        self.set_global_parameter("generate_at_creation", False)
        self.client.patch(
            reverse("v2:account-detail", args=[account.pk]), values, format="json"
        )
        self.assertTrue(os.path.exists(fname))

    def test_with_connection_settings(self):
        """Add connection settings to documents."""
        self.set_global_parameter("include_connection_settings", True)
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))

    def test_with_custom_message(self):
        """Add custom message to documents."""
        self.set_global_parameter("custom_message", "This is a test message.")
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))

    def test_account_delete(self):
        """Check that document is deleted with account."""
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))
        account = core_models.User.objects.get(username=values["username"])
        url = reverse("v2:account-delete", args=[account.pk])
        self.client.post(url)
        self.assertFalse(os.path.exists(fname))

    @override_settings(MODOBOA_LOGO="modoboa.png")
    def test_with_custom_logo(self):
        """Check that document is deleted with account."""
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))

    def test_download_and_delete_account(self):
        """Check that document is deleted with account."""
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))
        account = core_models.User.objects.get(username=values["username"])

        # Try to download the file
        response = self.client.get(reverse("v2:get-credentials", args=[account.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # File have been deleted?
        self.assertFalse(os.path.exists(fname))

        # Delete account
        url = reverse("v2:account-delete", args=[account.pk])
        self.client.post(url)
        self.assertFalse(os.path.exists(fname))

    def test_storage_dir_creation(self):
        """Test storage directory creation."""
        self.set_global_parameter("storage_dir", "/nonexistentdir")
        self._create_account("leon@test.com", expected_status=500)

    def test_directory_check_settings(self):
        """Test validation for unwritable directory."""
        self.set_global_parameter("storage_dir", "/nonexistentdir")
        self.set_global_parameter("enabled_pdfcredentials", False)
        url = reverse("v2:parameter-detail", args=["pdfcredentials"])
        data = {
            "webpanel_url": "http://localhost",
            "smtp_server_address": "mail.localhost",
            "imap_server_address": "mail.localhost",
        }

        # Test that we can't activate it without providing a valid storage dir.
        data["enabled_pdfcredentials"] = True
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Directory not found", resp.content)
        # Test that we can disable it even if the directory is not right.
        self.set_global_parameter("enabled_pdfcredentials", True)
        data["enabled_pdfcredentials"] = False
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
