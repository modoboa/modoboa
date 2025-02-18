"""PDF credentials tests."""

import os
import shutil
import tempfile

from django.test import override_settings
from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models

from modoboa.lib.tests import ModoTestCase


class EventsTestCase(ModoTestCase):
    """Test event handlers."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super().setUpTestData()
        admin_factories.DomainFactory(name="test.com")

    def setUp(self):
        """Create temp. directory to store files."""
        super().setUp()
        self.workdir = tempfile.mkdtemp()
        self.set_global_parameter("storage_dir", self.workdir)

    def tearDown(self):
        """Reset test env."""
        shutil.rmtree(self.workdir)

    def _create_account(self, username, expected_status=200):
        """Create a test account."""
        values = {
            "username": username,
            "first_name": "Tester",
            "last_name": "Toto",
            "role": "SimpleUsers",
            "quota_act": True,
            "is_active": True,
            "email": username,
            "random_password": True,
            "stepid": 2,
        }
        response = self.client.post(
            reverse("admin:account_add"), values, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, expected_status)
        return values

    def test_password_updated(self):
        """Check that document is generated at account creation/update."""
        values = self._create_account("leon@test.com")
        fname = os.path.join(self.workdir, "{}.pdf".format(values["username"]))
        self.assertTrue(os.path.exists(fname))
        account = core_models.User.objects.get(username=values["username"])

        # Check if link is present in listing page
        response = self.ajax_get(reverse("admin:_identity_list"))
        self.assertIn('name="get_credentials"', response["rows"])

        # Try to download the file
        response = self.client.get(
            reverse("pdfcredentials:account_credentials", args=[account.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # File have been deleted?
        self.assertFalse(os.path.exists(fname))

        # Try to download a second time
        response = self.client.get(
            reverse("pdfcredentials:account_credentials", args=[account.pk])
        )
        self.assertContains(response, "No document available for this user")

        # Update account
        values.update({"language": "en", "subject": "subject", "content": "content"})
        self.ajax_post(reverse("admin:account_change", args=[account.pk]), values)
        self.assertFalse(os.path.exists(fname))

        self.set_global_parameter("generate_at_creation", False)
        self.ajax_post(reverse("admin:account_change", args=[account.pk]), values)
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
        self.ajax_post(reverse("admin:account_delete", args=[account.pk]), {})
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
        response = self.client.get(
            reverse("pdfcredentials:account_credentials", args=[account.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # File have been deleted?
        self.assertFalse(os.path.exists(fname))

        # Delete account
        self.ajax_post(reverse("admin:account_delete", args=[account.pk]), {})

    def test_storage_dir_creation(self):
        """Test storage directory creation."""
        self.set_global_parameter("storage_dir", "/nonexistentdir")
        with self.assertLogs(logger="modoboa.admin", level="ERROR") as log:
            self._create_account("leon@test.com")
            self.assertIn(
                "ERROR:modoboa.admin:Failed to create PDF_credentials directory. "
                "Please check the permissions or the path.",
                log.output,
            )
