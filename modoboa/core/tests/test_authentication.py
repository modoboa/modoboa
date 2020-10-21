"""Tests for core application."""

import os
import smtplib
from unittest import mock, skipIf, skipUnless

from django.core import mail
from django.test import override_settings
from django.urls import reverse

try:
    import argon2
except ImportError:
    argon2 = None

from modoboa.core.password_hashers import (
    get_password_hasher, get_dovecot_schemes
)
from modoboa.lib.tests import NO_SMTP, ModoTestCase
from .. import factories, models


@override_settings(
    DOVEADM_LOOKUP_PATH=["{}/doveadm".format(os.path.dirname(__file__))])
class AuthenticationTestCase(ModoTestCase):
    """Validate authentication scenarios."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(AuthenticationTestCase, cls).setUpTestData()
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

    @mock.patch("django_otp.match_token")
    @mock.patch("django_otp.login")
    def test_authentication_with_2fa(self, login_mock, match_mock):
        user = models.User.objects.get(username="user@test.com")
        user.totpdevice_set.create(name="Device")
        user.tfa_enabled = True
        user.save()
        data = {"username": "user@test.com", "password": "toto"}
        response = self.client.post(reverse("core:login"), data)

        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 302)
        url = reverse("core:2fa_verify")
        self.assertTrue(response.url.endswith(url))

        match_mock.side_effect = [None, user.totpdevice_set.first()]
        data = {"tfa_code": "1234"}
        response = self.client.post(url, data)
        self.assertContains(response, "This code is invalid")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    def test_open_redirect(self):
        """Check that open redirect is not allowed."""
        self.client.logout()
        data = {"username": "admin", "password": "password"}

        # 1. Check valid redirection
        url = "{}?next=/admin/".format(reverse("core:login"))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("admin:index")))
        self.client.logout()

        # 2. Check bad redirection
        url = "{}?next=http://www.evil.com".format(reverse("core:login"))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:dashboard")))

    def test_password_schemes(self):
        """Validate password scheme changes."""
        username = "user@test.com"
        password = "toto"
        data = {"username": username, "password": password}
        user = models.User.objects.get(username=username)
        pw_hash = get_password_hasher('fallback_scheme')()

        self.client.logout()
        self.set_global_parameter("password_scheme", "sha512crypt")
        self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("{SHA512-CRYPT}"))

        self.client.logout()
        self.set_global_parameter("password_scheme", "sha256")
        self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("{SHA256}"))

        if argon2 is not None:
            self.client.logout()
            self.set_global_parameter("password_scheme", "argon2id")
            self.client.post(reverse("core:login"), data)
            user.refresh_from_db()
            self.assertTrue(user.password.startswith("{ARGON2ID}"))

        self.client.logout()
        self.set_global_parameter("password_scheme", "fallback_scheme")
        self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith(pw_hash.scheme))

        self.client.logout()
        self.set_global_parameter("password_scheme", "sha256crypt")
        self.set_global_parameter("update_scheme", False)
        self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith(pw_hash.scheme))

    @skipUnless(argon2, "argon2-cffi not installed")
    def test_password_argon2_parameter_change(self):
        """Validate hash parameter update on login works with argon2."""
        username = "user@test.com"
        password = "toto"
        data = {"username": username, "password": password}
        user = models.User.objects.get(username=username)
        self.set_global_parameter("password_scheme", "argon2id")

        self.client.logout()
        with self.settings(
            MODOBOA_ARGON2_TIME_COST=4,
            MODOBOA_ARGON2_MEMORY_COST=10000,
            MODOBOA_ARGON2_PARALLELISM=4,
        ):
            self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("{ARGON2ID}"))
        parameters = argon2.extract_parameters(
            user.password.lstrip("{ARGON2ID}")
        )
        self.assertEqual(parameters.time_cost, 4)
        self.assertEqual(parameters.memory_cost, 10000)
        self.assertEqual(parameters.parallelism, 4)

        self.client.logout()
        with self.settings(
            MODOBOA_ARGON2_TIME_COST=3,
            MODOBOA_ARGON2_MEMORY_COST=1000,
            MODOBOA_ARGON2_PARALLELISM=2,
        ):
            self.client.post(reverse("core:login"), data)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("{ARGON2ID}"))
        parameters = argon2.extract_parameters(
            user.password.lstrip("{ARGON2ID}"))
        self.assertEqual(parameters.time_cost, 3)
        self.assertEqual(parameters.memory_cost, 1000)
        self.assertEqual(parameters.parallelism, 2)

    def test_supported_schemes(self):
        """Validate dovecot supported schemes."""
        supported_schemes = get_dovecot_schemes()
        self.assertEqual(supported_schemes,
                         ["{MD5}",
                          "{MD5-CRYPT}",
                          "{SHA}",
                          "{SHA1}",
                          "{SHA256}",
                          "{SHA512}",
                          "{SMD5}",
                          "{SSHA}",
                          "{SSHA256}",
                          "{SSHA512}",
                          "{PLAIN}",
                          "{CLEAR}",
                          "{CLEARTEXT}",
                          "{PLAIN-TRUNC}",
                          "{CRAM-MD5}",
                          "{SCRAM-SHA-1}",
                          "{HMAC-MD5}",
                          "{DIGEST-MD5}",
                          "{PLAIN-MD4}",
                          "{PLAIN-MD5}",
                          "{LDAP-MD5}",
                          "{LANMAN}",
                          "{NTLM}",
                          "{OTP}",
                          "{SKEY}",
                          "{RPA}",
                          "{PBKDF2}",
                          "{CRYPT}",
                          "{SHA256-CRYPT}",
                          "{SHA512-CRYPT}"])


class PasswordResetTestCase(ModoTestCase):
    """Test password reset service."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(PasswordResetTestCase, cls).setUpTestData()
        cls.account_ok = factories.UserFactory(
            username="user@test.com", secondary_email="test@ext.com",
            phone_number="+33612345678",
            groups=("SimpleUsers",)
        )
        cls.account_ko = factories.UserFactory(
            username="user2@test.com", groups=("SimpleUsers",)
        )

    def test_reset_password(self):
        """Validate simple case."""
        self.client.logout()
        url = reverse("password_reset")
        data = {"email": self.account_ok.email}
        response = self.client.post(url, data, follow=True)
        self.assertContains(
            response,
            "We've emailed you instructions for setting your password")
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_password_no_secondary_email(self):
        """Check email is not sent."""
        self.client.logout()
        url = reverse("password_reset")
        data = {"email": self.account_ko.email}
        response = self.client.post(url, data, follow=True)
        self.assertContains(
            response,
            "We've emailed you instructions for setting your password")
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_password_announcement(self):
        """Check if announcement is showing."""
        self.client.logout()
        url = reverse("password_reset")
        msg = "Announcement"
        self.set_global_parameter("password_recovery_msg", msg)
        response = self.client.get(url)
        self.assertContains(response, msg)

    @mock.patch("oath.accept_totp")
    @mock.patch("ovh.Client.get")
    @mock.patch("ovh.Client.post")
    def test_reset_password_sms(self, client_post, client_get, accept_totp):
        """Test reset password by SMS."""
        client_get.return_value = ["service"]
        client_post.return_value = {"totalCreditsRemoved": 1}
        self.set_global_parameters({
            "sms_password_recovery": True,
            "sms_provider": "ovh",
            "sms_ovh_application_key": "key",
            "sms_ovh_application_secret": "secret",
            "sms_ovh_consumer_key": "consumer"
        })
        self.client.logout()
        url = reverse("password_reset")
        data = {"email": self.account_ok.email}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("password_reset_confirm_code"))

        data = {"code": "123456"}
        url = reverse("password_reset_confirm_code")
        accept_totp.return_value = (False, "")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        accept_totp.return_value = (True, "")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

    @mock.patch("ovh.Client.get")
    @mock.patch("ovh.Client.post")
    def test_resend_reset_code(self, client_post, client_get):
        """Test resend code service."""
        url = reverse("password_reset_resend_code")
        # SMS password recovery not enabled
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        self.set_global_parameters({
            "sms_password_recovery": True,
            "sms_provider": "ovh",
            "sms_ovh_application_key": "key",
            "sms_ovh_application_secret": "secret",
            "sms_ovh_consumer_key": "consumer"
        }, app="core")
        # No user pk in session
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        session = self.client.session
        session["user_pk"] = self.account_ok.pk
        session.save()
        client_get.return_value = ["service"]
        client_post.return_value = {"totalCreditsRemoved": 1}
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("totp_secret", self.client.session)


@skipIf(NO_SMTP, "No SMTP server available")
@override_settings(AUTHENTICATION_BACKENDS=(
    "modoboa.lib.authbackends.SMTPBackend",
    "django.contrib.auth.backends.ModelBackend"
))
class SMTPAuthenticationTestCase(ModoTestCase):
    """Validate SMTP authentication scenarios."""

    def _test_smtp_authentication(self, mock_smtp):
        """Common code to check authentication"""
        self.client.logout()
        username = "user@unknown.test"
        password = "toto"
        data = {"username": username, "password": password}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:user_index")))
        mock_smtp.return_value.login.assert_called_once_with(
            username, password)
        self.assertTrue(
            models.User.objects.filter(username=username).exists())

    @mock.patch("smtplib.SMTP")
    def test_smtp_authentication(self, mock_smtp):
        """Check simple SMTP authentication."""
        self._test_smtp_authentication(mock_smtp)

    @mock.patch("smtplib.SMTP_SSL")
    @override_settings(AUTH_SMTP_SECURED_MODE="ssl")
    def test_smtp_authentication_over_ssl(self, mock_smtp):
        """Check SMTP authentication over SSL."""
        self._test_smtp_authentication(mock_smtp)

    @mock.patch("smtplib.SMTP")
    @override_settings(AUTH_SMTP_SECURED_MODE="starttls")
    def test_smtp_authentication_over_starttls(self, mock_smtp):
        """Check SMTP authentication over STARTTLS."""
        self._test_smtp_authentication(mock_smtp)

    @mock.patch("smtplib.SMTP")
    def test_smtp_authentication_failure(self, mock_smtp):
        """Check SMTP authentication failure."""
        instance = mock_smtp.return_value
        instance.login.side_effect = smtplib.SMTPAuthenticationError(
            450, "User not found")
        self.client.logout()
        username = "user@unknown.test"
        password = "toto"
        data = {"username": username, "password": password}
        response = self.client.post(reverse("core:login"), data)
        self.assertEqual(response.status_code, 401)
        mock_smtp.return_value.login.assert_called_once_with(
            username, password)
        self.assertFalse(
            models.User.objects.filter(username=username).exists())
