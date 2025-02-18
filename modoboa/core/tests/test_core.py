"""Tests for core application."""

from io import StringIO

import httmock
from dateutil.relativedelta import relativedelta
from oauth2_provider.models import get_application_model

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
        self.assertTrue(response.url.endswith(reverse("core:user_index")))

        response = self.client.post(reverse("core:logout"), {})
        self.assertEqual(response.status_code, 302)

        data = {"username": "admin", "password": "password"}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:dashboard")))


class ManagementCommandsTestCase(SimpleModoTestCase):
    """Test management commands."""

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

    def test_non_duplicate_client_creation(self):
        """Test that the load_initial_data command do not create duplicates
        client for the frontend deployment."""
        app_model = get_application_model()
        management.call_command("load_initial_data")
        self.assertEqual(1, app_model.objects.filter(name="modoboa_frontend").count())
        management.call_command("load_initial_data")
        self.assertEqual(1, app_model.objects.filter(name="modoboa_frontend").count())

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


class ProfileTestCase(ModoTestCase):
    """Profile related tests."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=("SimpleUsers",)
        )

    def test_update_profile(self):
        """Update profile without password."""
        data = {
            "first_name": "Homer",
            "last_name": "Simpson",
            "phone_number": "+33612345678",
            "language": "en",
        }
        self.ajax_post(reverse("core:user_profile"), data)
        admin = models.User.objects.get(username="admin")
        self.assertEqual(admin.last_name, "Simpson")

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        self.ajax_post(
            reverse("core:user_profile"),
            {
                "language": "en",
                "oldpassword": "password",
                "newpassword": "12345Toi",
                "confirmation": "12345Toi",
            },
        )
        self.client.logout()

        self.assertEqual(self.client.login(username="admin", password="12345Toi"), True)
        self.assertEqual(
            self.client.login(username="user@test.com", password="toto"), True
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {"language": "en", "oldpassword": "toto", "confirmation": "tutu"},
            status=400,
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {"language": "en", "oldpassword": "toto", "newpassword": "tutu"},
            status=400,
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {
                "language": "en",
                "oldpassword": "toto",
                "newpassword": "tutu",
                "confirmation": "tutu",
            },
            status=400,
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {
                "language": "en",
                "oldpassword": "toto",
                "newpassword": "Toto1234",
                "confirmation": "Toto1234",
            },
        )
        self.client.logout()
        self.assertTrue(
            self.client.login(username="user@test.com", password="Toto1234")
        )

    def test_update_password_restrictions(self):
        self.ajax_post(
            reverse("core:user_profile"),
            {
                "language": "en",
                "oldpassword": "",
                "newpassword": "12345Toi",
                "confirmation": "12345Toi",
            },
            status=400,
        )
        self.client.logout()

        self.assertEqual(
            self.client.login(username="admin", password="12345Toi"), False
        )

    def test_update_password_url(self):
        """Check if external is used when defined."""
        self.set_global_parameter("update_password_url", "http://update.password")
        non_local_user = factories.UserFactory(
            username="user@external.com", groups=("SimpleUsers",), is_local=False
        )
        self.client.force_login(non_local_user)
        url = reverse("core:user_profile")
        response = self.client.get(url)
        self.assertContains(response, "http://update.password")

        self.client.force_login(self.account)
        response = self.client.get(url)
        self.assertNotContains(response, "http://update.password")


class APIAccessFormTestCase(ModoTestCase):
    """Check form access."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=("SimpleUsers",)
        )

    def test_form_access(self):
        """Check access restrictions."""
        url = reverse("core:user_api_access")
        self.ajax_get(url)
        self.client.logout()
        self.client.login(username="user@test.com", password="toto")
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 278)

    def test_form(self):
        """Check that token is created/removed."""
        url = reverse("core:user_api_access")
        self.ajax_post(url, {"enable_api_access": True})
        user = models.User.objects.get(username="admin")
        self.assertTrue(hasattr(user, "auth_token"))
        self.ajax_post(url, {"enable_api_access": False})
        user = models.User.objects.get(username="admin")
        self.assertFalse(hasattr(user, "auth_token"))


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

        url = reverse("core:information")
        response = self.ajax_request("get", url)
        self.assertIn("9.0.0", response["content"])

        # Enable notifications
        self.set_global_parameter("send_new_versions_email", True)
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
