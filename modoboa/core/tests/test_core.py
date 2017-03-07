"""Tests for core application."""

import httmock

from django.core import management
from django.core.urlresolvers import reverse
from django.test import TestCase

from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import mocks
from .. import models


class AuthenticationTestCase(ModoTestCase):

    """Validate authentication scenarios."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(AuthenticationTestCase, cls).setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
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


class LoadInitialDataTestCase(TestCase):
    """Try to change the default username."""

    def test_change_default_admin(self):
        """Use dedicated option."""
        management.call_command(
            "load_initial_data", "--admin-username", "modoadmin")
        self.assertTrue(
            self.client.login(username="modoadmin", password="password"))

    def test_set_secret_key(self):
        """Use dedicated option."""
        management.call_command("load_initial_data")
        lc = models.LocalConfig.objects.first()
        self.assertIn("core", lc._parameters)
        self.assertIn("secret_key", lc._parameters["core"])


class ProfileTestCase(ModoTestCase):
    """Profile related tests."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ProfileTestCase, cls).setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
        )

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        self.ajax_post(reverse("core:user_profile"),
                       {"language": "en", "oldpassword": "password",
                        "newpassword": "12345Toi", "confirmation": "12345Toi"})
        self.client.logout()

        self.assertEqual(
            self.client.login(username="admin", password="12345Toi"), True
        )
        self.assertEqual(
            self.client.login(username="user@test.com", password="toto"), True
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {"oldpassword": "toto",
             "newpassword": "tutu", "confirmation": "tutu"},
            status=400
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {"language": "en", "oldpassword": "toto",
             "newpassword": "Toto1234", "confirmation": "Toto1234"}
        )
        self.client.logout()
        self.assertTrue(
            self.client.login(username="user@test.com", password="Toto1234")
        )


class APIAccessFormTestCase(ModoTestCase):

    """Check form access."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(APIAccessFormTestCase, cls).setUpTestData()
        cls.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
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
                mocks.modo_api_versions):
            management.call_command("communicate_with_public_api")
        self.assertEqual(models.LocalConfig.objects.first().api_pk, 100)

        url = reverse("core:information")
        response = self.ajax_request("get", url)
        self.assertIn("9.0.0", response["content"])
