"""Tests for core application."""

from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase
from . import factories


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
        self.clt.logout()
        data = {"username": "user@test.com", "password": "toto"}
        response = self.clt.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:user_index")))

        response = self.clt.post(reverse("core:logout"), {})
        self.assertEqual(response.status_code, 302)

        data = {"username": "admin", "password": "password"}
        response = self.clt.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("admin:domain_list")))


class ProfileTestCase(ModoTestCase):

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
        self.clt.logout()

        self.assertEqual(
            self.clt.login(username="admin", password="12345Toi"), True
        )
        self.assertEqual(
            self.clt.login(username="user@test.com", password="toto"), True
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
        self.clt.logout()
        self.assertTrue(
            self.clt.login(username="user@test.com", password="Toto1234")
        )
