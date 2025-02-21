"""Tests for core application."""

from io import StringIO
import json
import pathlib
import shutil

import httmock
from dateutil.relativedelta import relativedelta
from oauth2_provider.models import get_application_model

from django.conf import settings
from django.core import mail
from django.core import management
from django.urls import reverse
from django.utils import timezone

from modoboa.lib.tests import ModoTestCase, SimpleModoTestCase
from .. import factories, mocks, models


class AuthenticationTestCase(ModoTestCase):
    """Validate authentication scenarios."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=("SimpleUsers",)
        )

    def test_authentication(self):
        """Validate simple case."""
        self.client.logout()
        data = {"username": "user@test.com", "password": "toto"}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse("core:logout"), {})
        self.assertEqual(response.status_code, 302)

        data = {"username": "admin", "password": "password"}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)


class ManagementCommandsTestCase(SimpleModoTestCase):
    """Test management commands."""

    def tearDown(self):
        frontend_dir = pathlib.Path(settings.BASE_DIR) / "frontend"
        if frontend_dir.exists():
            shutil.rmtree(frontend_dir)

    def test_change_default_admin(self):
        """Use dedicated option."""
        management.call_command("load_initial_data", "--admin-username", "modoadmin")
        self.assertTrue(self.client.login(username="modoadmin", password="password"))

    def test_clean_logs(self):
        """Run cleanlogs command."""
        log1 = factories.LogFactory()
        factories.LogFactory()
        log1.date_created -= relativedelta(years=2)
        log1.save(update_fields=["date_created"])
        management.call_command("cleanlogs")
        self.assertEqual(models.Log.objects.count(), 1)

    def test_init_data_non_duplicate_client_creation(self):
        """Test that the load_initial_data command does not create duplicates
        client for the frontend deployment."""
        app_model = get_application_model()
        management.call_command("load_initial_data")
        self.assertEqual(1, app_model.objects.filter(name="modoboa_frontend").count())
        management.call_command("load_initial_data")
        self.assertEqual(1, app_model.objects.filter(name="modoboa_frontend").count())

    def test_init_data_frontend_dir_creation(self):
        """Test that the load_initial_data command creates a frontend directory
        with symlinks to the shipped frontend files."""
        # Create our own dummy frontend directory if `vite` hasn’t been invoked yet
        frontend_src = pathlib.Path(__file__).parent.parent.parent / "frontend_dist"
        if not frontend_src.is_dir():
            (frontend_src / "dummy").mkdir(parents=True)
            self.addCleanup(shutil.rmtree, frontend_src)

        frontend_dir = pathlib.Path(settings.BASE_DIR) / "frontend"
        self.assertFalse(frontend_dir.exists(), f"frontend directory {frontend_dir} doesn’t exist before load_initial_data")
        management.call_command("load_initial_data")
        self.assertTrue(frontend_dir.is_dir(), f"frontend directory {frontend_dir} is directory after load_initial_data")
        for entry in frontend_dir.iterdir():
            if entry.name == "config.json":
                self.assertTrue(entry.is_file() and not entry.is_symlink(), f"frontend directory entry {entry} is regular file")
                try:
                    content = json.loads(entry.read_text("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self.fail(f"frontend directory entry {entry} is not UTF-8 encoded JSON")
                for key_name in ("API_BASE_URL", "OAUTH_AUTHORITY_URL", "OAUTH_CLIENT_ID", "OAUTH_REDIRECT_URI", "OAUTH_POST_REDIRECT_URI"):
                    self.assertIn(key_name, content)
            else:
                self.assertTrue(entry.is_symlink(), f"frontend directory entry {entry} is symlink")

    def test_clean_inactive_accounts(self):
        """Run clean_inactive_accounts command."""
        management.call_command("load_initial_data")

        # no inactive account, should exit normaly
        management.call_command("clean_inactive_accounts")

        last_login = timezone.now() - relativedelta(days=45)
        account = factories.UserFactory(
            username="user1@domain.test", groups=("SimpleUsers",), last_login=last_login
        )
        management.call_command("clean_inactive_accounts", "--dry-run")
        account.refresh_from_db()
        self.assertTrue(account.is_active)

        out = StringIO()
        management.call_command(
            "clean_inactive_accounts", "--verbose", "--dry-run", stdout=out
        )
        self.assertIn("user1@domain.test", out.getvalue())

        # Disable account account threshold
        self.set_global_parameter("enable_inactive_accounts", False)
        out = StringIO()
        management.call_command("clean_inactive_accounts", "--verbose", stdout=out)
        self.assertIn("Inactive accounts detection is disabled.", out.getvalue())

        self.set_global_parameter("enable_inactive_accounts", True)
        management.call_command("clean_inactive_accounts", "--silent")
        account.refresh_from_db()
        self.assertFalse(account.is_active)

        account.is_active = True
        account.save(update_fields=["is_active"])

        management.call_command("clean_inactive_accounts", "--silent", "--delete")
        with self.assertRaises(models.User.DoesNotExist):
            account.refresh_from_db()


class APICommunicationTestCase(ModoTestCase):
    """Check communication with the API."""

    def test_management_command(self):
        """Check command."""
        with httmock.HTTMock(
            mocks.modo_api_instance_search,
            mocks.modo_api_instance_create,
            mocks.modo_api_instance_update,
            mocks.modo_api_versions,
        ):
            management.call_command("communicate_with_public_api")
        self.assertEqual(models.LocalConfig.objects.first().api_pk, 100)
        self.assertEqual(len(mail.outbox), 0)

        # Enable notifications
        self.set_global_parameter("send_new_versions_email", True)
        self.set_global_parameter("new_versions_email_rcpt", "postmaster@domain.test")
        with httmock.HTTMock(
            mocks.modo_api_instance_search,
            mocks.modo_api_instance_create,
            mocks.modo_api_instance_update,
            mocks.modo_api_versions,
        ):
            management.call_command("communicate_with_public_api")
        self.assertEqual(len(mail.outbox), 1)

        # Call once again and check no new notification has been sent
        self.set_global_parameter("send_new_versions_email", True)
        with httmock.HTTMock(
            mocks.modo_api_instance_search,
            mocks.modo_api_instance_create,
            mocks.modo_api_instance_update,
            mocks.modo_api_versions,
        ):
            management.call_command("communicate_with_public_api")
        self.assertEqual(len(mail.outbox), 1)

        # Make sure no new notification is sent when no updates
        with httmock.HTTMock(
            mocks.modo_api_instance_search,
            mocks.modo_api_instance_create,
            mocks.modo_api_instance_update,
            mocks.modo_api_versions_no_update,
        ):
            management.call_command("communicate_with_public_api")
        self.assertEqual(len(mail.outbox), 1)
