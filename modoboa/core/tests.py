"""Tests for core application."""

from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase
from . import factories


class ProfileTestCase(ModoTestCase):

    def setUp(self):
        super(ProfileTestCase, self).setUp()
        self.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
        )

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        self.ajax_post(reverse("core:user_profile"),
                       {"oldpassword": "password",
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
            {"oldpassword": "toto",
             "newpassword": "Toto1234", "confirmation": "Toto1234"}
        )
        self.clt.logout()
        self.assertTrue(
            self.clt.login(username="user@test.com", password="Toto1234")
        )
