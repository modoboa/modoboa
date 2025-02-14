"""Core API related tests."""

import copy
import getpass
import oath
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from modoboa.admin import (
    factories,
    models as admin_models,
    constants as admin_constants,
)
from modoboa.core import models, constants
from modoboa.core.tests import utils
from modoboa.lib.tests import ModoAPITestCase
from rest_framework.authtoken.models import Token

DOVEADM_TEST_PATH = utils.get_doveadm_test_path()
DOVECOT_USER = getpass.getuser()

CORE_SETTINGS = {
    "authentication_type": "local",
    "password_scheme": "sha512crypt",
    "rounds_number": 70000,
    "update_scheme": True,
    "default_password": "Toto12345",
    "random_password_length": 8,
    "update_password_url": "",
    "password_recovery_msg": "",
    "sms_password_recovery": False,
    "ldap_server_address": "localhost",
    "ldap_server_port": 389,
    "ldap_enable_secondary_server": False,
    "ldap_secondary_server_address": "localhost",
    "ldap_secondary_server_port": 389,
    "ldap_secured": "none",
    "ldap_is_active_directory": False,
    "ldap_admin_groups": "",
    "ldap_group_type": "posixgroup",
    "ldap_groups_search_base": "",
    "ldap_password_attribute": "userPassword",
    "ldap_auth_method": "searchbind",
    "ldap_bind_dn": "",
    "ldap_bind_password": "",
    "ldap_search_base": "",
    "ldap_search_filter": "(mail=%(user)s)",
    "ldap_user_dn_template": "",
    "ldap_sync_bind_dn": "",
    "ldap_sync_bind_password": "",
    "ldap_enable_sync": False,
    "ldap_sync_delete_remote_account": False,
    "ldap_sync_account_dn_template": "",
    "ldap_enable_import": False,
    "ldap_import_search_base": "",
    "ldap_import_search_filter": "(cn=*)",
    "ldap_import_username_attr": "cn",
    "ldap_dovecot_sync": False,
    "ldap_dovecot_conf_file": "/etc/dovecot/dovecot-modoboa.conf",
    "rss_feed_url": "",
    "hide_features_widget": False,
    "sender_address": "noreply@yourdomain.test",
    "enable_api_communication": True,
    "check_new_versions": True,
    "send_new_versions_email": False,
    "new_versions_email_rcpt": "postmaster@yourdomain.test",
    "send_statistics": True,
    "enable_inactive_accounts": True,
    "inactive_account_threshold": 30,
    "top_notifications_check_interval": 30,
    "log_maximum_age": 365,
    "items_per_page": 30,
    "default_top_redirection": "user",
}


class ParametersAPITestCase(ModoAPITestCase):
    def setUp(self):
        super().setUp()
        cache.delete("password_scheme_choice")

    @override_settings(
        DOVEADM_LOOKUP_PATH=[DOVEADM_TEST_PATH], DOVECOT_USER=DOVECOT_USER
    )
    def test_update(self):
        url = reverse("v2:parameter-global-detail", args=["core"])
        data = copy.copy(CORE_SETTINGS)
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        self.assertIsNotNone(cache.get("password_scheme_choice"))
        self.assertIn(("plain", "plain (weak)"), cache.get("password_scheme_choice"))
        # Modify SMS related settings
        data["sms_password_recovery"] = True
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("sms_provider", resp.json())
        data["sms_provider"] = "test"
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        data.update(
            {
                "sms_provider": "ovh",
                "sms_ovh_application_key": "key",
                "sms_ovh_application_secret": "secret",
                "sms_ovh_consumer_key": "consumer",
            }
        )
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        # Modify some LDAP settings
        data.update({"authentication_type": "ldap", "ldap_auth_method": "searchbind"})
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ldap_search_base", resp.json())

        data.update({"ldap_auth_method": "directbind"})
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ldap_user_dn_template", resp.json())

        data.update(
            {
                "ldap_user_dn_template": "%(user)s",
                "ldap_sync_account_dn_template": "%(user)s",
                "ldap_search_filter": "mail=%(user)s",
            }
        )
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_doveadm_alarm(self):
        """Test that an alarm is opened, closed or reopened
        depending on the result of the doveadm command for the password scheme
        """
        # Test case where doveadm command fails
        url = reverse("v2:parameter-global-detail", args=["core"])
        data = copy.copy(CORE_SETTINGS)
        data["password_scheme"] = "plain"

        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        self.assertIsNone(cache.get("password_scheme_choice"))
        doveadm_alarm = admin_models.Alarm.objects.filter(
            internal_name=constants.DOVEADM_PASS_SCHEME_ALARM
        )
        self.assertEqual(doveadm_alarm.count(), 1)
        cache.delete("job_cache_available_password_hasher")

        with self.settings(
            DOVEADM_LOOKUP_PATH=[DOVEADM_TEST_PATH], DOVECOT_USER=DOVECOT_USER
        ):
            # The command should work and close the alarm
            resp = self.client.put(url, data, format="json")
            self.assertEqual(resp.status_code, 200)

            self.assertIsNotNone(cache.get("password_scheme_choice"))
            doveadm_alarm = admin_models.Alarm.objects.filter(
                internal_name=constants.DOVEADM_PASS_SCHEME_ALARM
            )
            self.assertEqual(doveadm_alarm.count(), 1)
            self.assertEqual(doveadm_alarm.first().status, admin_constants.ALARM_CLOSED)
            cache.delete("job_cache_available_password_hasher")

        # And lastly check that the alarm is reopened if the issue starts again
        # Simulate that the cache has expired
        cache.delete("password_scheme_choice")
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        doveadm_alarm = admin_models.Alarm.objects.filter(
            internal_name=constants.DOVEADM_PASS_SCHEME_ALARM
        )
        self.assertEqual(doveadm_alarm.count(), 1)
        self.assertEqual(doveadm_alarm.first().status, admin_constants.ALARM_OPENED)


class AccountViewSetTestCase(ModoAPITestCase):
    def test_me(self):
        url = reverse("v2:account-me")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        me = resp.json()
        self.assertEqual(me["username"], "admin")

    def test_me_password(self, password_ko="Toto1234", password_ok="password"):
        url = reverse("v2:account-check-me-password")
        resp = self.client.post(url, {"password": password_ko}, format="json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(url, {"password": password_ok}, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_tfa_setup(self):
        # Setup TFA
        url = reverse("v2:account-tfa-setup-get-key")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        user = models.User.objects.get(username="admin")
        user.totpdevice_set.create(name="Device")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/json")

        user.totp_enabled = True
        user.save()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @mock.patch("django_otp.plugins.otp_totp.models.TOTPDevice.verify_token")
    def test_tfa_setup_modify(
        self, verify_mock, password_ko="Toto1234", password_ok="password"
    ):
        user = models.User.objects.get(username="admin")
        user.totpdevice_set.create(name="Device")

        url = reverse("v2:account-tfa-setup-check")
        data = {"pin_code": 1234}
        verify_mock.side_effect = [False]
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        verify_mock.side_effect = [True]
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("tokens", resp.json())

        verify_mock.side_effect = [True]
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        url_reset = reverse("v2:account-tfa-reset-codes")
        url_disable = reverse("v2:account-tfa-disable")
        data = {"password": password_ko}
        # Try regenerate TFA backup code with wrong password
        resp = self.client.post(url_reset, data, format="json")
        self.assertEqual(resp.status_code, 400)
        # Try disable with wrong password
        resp = self.client.post(url_disable, data, format="json")
        self.assertEqual(resp.status_code, 400)

        # Test with password ok
        data = {"password": password_ok}
        # Try regenerate TFA backup codes with good password
        resp = self.client.post(url_reset, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("tokens", resp.json())

        # Try disable with good password
        resp = self.client.post(url_disable, data, format="json")
        self.assertEqual(resp.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.totp_enabled, False)


class PasswordResetTestCase(AccountViewSetTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 0
        self.sms_token = 0

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=models.User.objects.get(username="admin@test.com")
        )

    @mock.patch("ovh.Client.get")
    @mock.patch("ovh.Client.post")
    def test_reset_password(self, client_post, client_get):
        url = reverse("v2:password_reset")
        # No payload provided
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

        # Invalid user
        data = {"email": "doesntexist@whoami.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["type"], "sms")

        account = models.User.objects.get(username="user@test.com")

        # Email reset test
        # No secondary email
        data = {"email": account.email}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["type"], "email")
        # With secondary email
        account.secondary_email = "toto@test.com"
        account.is_active = True
        account.save()
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "email")

        # SMS reset test
        self.set_global_parameters(
            {
                "sms_password_recovery": True,
                "sms_provider": "ovh",
                "sms_ovh_application_key": "key",
                "sms_ovh_application_secret": "secret",
                "sms_ovh_consumer_key": "consumer",
            },
            app="core",
        )

        # Phone number
        account.phone_number = "+33612345678"
        account.save()
        client_get.return_value = ["service"]
        client_post.return_value = {"totalCreditsRemoved": 1}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "sms")

    @mock.patch("ovh.Client.get")
    @mock.patch("ovh.Client.post")
    def test_password_reset_sms_totp(self, client_post, client_get):
        """Test reset password by SMS."""
        url_create_sms = reverse("v2:password_reset")
        url_sms_totp = reverse("v2:sms_totp")

        # Prepare account
        account = models.User.objects.get(username="user@test.com")
        account.phone_number = "+33612345678"
        account.secondary_email = "toto@test.com"
        account.is_active = True
        account.save()

        # Send sms
        client_get.return_value = ["service"]
        client_post.return_value = {"totalCreditsRemoved": 1}
        self.set_global_parameters(
            {
                "sms_password_recovery": True,
                "sms_provider": "ovh",
                "sms_ovh_application_key": "key",
                "sms_ovh_application_secret": "secret",
                "sms_ovh_consumer_key": "consumer",
            }
        )
        self.client.logout()
        self.create_session()
        data = {"email": account.email}
        response = self.client.post(url_create_sms, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "sms")
        self.assertIn("totp_secret", self.client.session)

        # Get the secret
        session = self.client.session
        secret = session["totp_secret"]

        # Fail to provide type
        data = {"sms_totp": "123456"}
        response = self.client.post(url_sms_totp, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Resend sms
        data = {"type": "resend"}
        response = self.client.post(url_sms_totp, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["type"], "resend")

        # False totp code
        data = {"sms_totp": "123456", "type": "confirm"}
        response = self.client.post(url_sms_totp, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["reason"], "Wrong totp")

        # Good totp code
        data = {"sms_totp": oath.totp(secret), "type": "confirm"}
        response = self.client.post(url_sms_totp, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json())
        self.assertIn("id", response.json())

    @mock.patch("ovh.Client.get")
    @mock.patch("ovh.Client.post")
    def test_password_change(self, client_post, client_get):
        url = reverse("v2:password_reset_confirm_v2")
        url_create_sms = reverse("v2:password_reset")
        url_sms_totp = reverse("v2:sms_totp")

        client_get.return_value = ["service"]
        client_post.return_value = {"totalCreditsRemoved": 1}
        self.set_global_parameters(
            {
                "sms_password_recovery": True,
                "sms_provider": "ovh",
                "sms_ovh_application_key": "key",
                "sms_ovh_application_secret": "secret",
                "sms_ovh_consumer_key": "consumer",
            }
        )

        # Prepare account
        account = models.User.objects.get(username="user@test.com")
        account.phone_number = "+33612345678"
        account.secondary_email = "toto@test.com"
        account.is_active = True
        account.save()

        # Send SMS
        self.create_session()
        data = {"email": account.email}
        response = self.client.post(url_create_sms, data, format="json")
        self.assertEqual(response.status_code, 200)
        session = self.client.session
        secret = session["totp_secret"]
        # Get token and ID
        data = {"sms_totp": oath.totp(secret), "type": "confirm"}
        response = self.client.post(url_sms_totp, data, format="json")
        self.assertEqual(response.status_code, 200)
        id_ok = response.json()["id"]
        token_ok = response.json()["token"]

        # Password differs
        data = {
            "new_password1": "123456",
            "new_password2": "123457",
            "token": token_ok,
            "id": id_ok,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

        # Wrong ID
        id_ko = urlsafe_base64_encode(force_bytes(-1))
        data = {
            "new_password1": "123456",
            "new_password2": "123456",
            "token": token_ok,
            "id": id_ko,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 404)

        # Wrong Token
        token_ko = "123456"
        data = {
            "new_password1": "123456",
            "new_password2": "123456",
            "token": token_ko,
            "id": id_ok,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)

        # Failed password requirements
        data = {
            "new_password1": "123456",
            "new_password2": "123456",
            "token": token_ok,
            "id": id_ok,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.json()["type"], "password_requirement")

        # All good
        data = {
            "new_password1": "MyHardenedPass1!",
            "new_password2": "MyHardenedPass1!",
            "token": token_ok,
            "id": id_ok,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        # TODO: See why user doesn't update it's password --> self.test_me_password(password_ok="MyHardenedPass1!")


class LanguageViewSetTestCase(ModoAPITestCase):
    def test_list(self):
        url = reverse("v2:language-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


class ComponentAPITestCase(ModoAPITestCase):
    def test_information(self):
        url = reverse("v2:components_information")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)


class NotificationAPITestCase(ModoAPITestCase):

    def test_get_notifications(self):
        url = reverse("v2:notifications")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 0)

        self.set_global_parameter("password_scheme", "crypt")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)


class AuthenticatorData(bytes):

    credential_data = b"RESPONSE"


class FIDOViewSetTestCase(ModoAPITestCase):

    @mock.patch("fido2.server.Fido2Server.register_complete")
    def test_registration(self, register_complete_mock):
        url = reverse("v2:fido-registration-begin")
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        register_complete_mock.side_effect = [AuthenticatorData()]
        data = {
            "type": "type",
            "id": "XX",
            "rawId": "XX",
            "authenticatorAttachment": "attachment",
            "response": {"key": "value"},
            "name": "Name",
        }
        url = reverse("v2:fido-registration-end")
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("tokens", resp.json())
