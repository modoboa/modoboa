"""Core API related tests."""

import copy
from unittest import mock

from django.urls import reverse

from modoboa.core import models
from modoboa.lib.tests import ModoAPITestCase

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
    "inactive_account_threshold": 30,
    "top_notifications_check_interval": 30,
    "log_maximum_age": 365,
    "items_per_page": 30,
    "default_top_redirection": "user"
}


class ParametersAPITestCase(ModoAPITestCase):

    def test_update(self):
        url = reverse("v2:parameter-detail", args=["core"])
        data = copy.copy(CORE_SETTINGS)
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        # Modify SMS related settings
        data["sms_password_recovery"] = True
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("sms_provider", resp.json())
        data["sms_provider"] = "test"
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        data.update({
            "sms_provider": "ovh",
            "sms_ovh_application_key": "key",
            "sms_ovh_application_secret": "secret",
            "sms_ovh_consumer_key": "consumer"
        })
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        # Modify some LDAP settings
        data.update({
            "authentication_type": "ldap",
            "ldap_auth_method": "searchbind"
        })
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ldap_search_base", resp.json())

        data.update({"ldap_auth_method": "directbind"})
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ldap_user_dn_template", resp.json())

        data.update({
            "ldap_user_dn_template": "%(user)s",
            "ldap_sync_account_dn_template": "%(user)s",
            "ldap_search_filter": "mail=%(user)s"
        })
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)


class AccountViewSetTestCase(ModoAPITestCase):

    def test_me(self):
        url = reverse("v2:account-me")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        me = resp.json()
        self.assertEqual(me["username"], "admin")

    def test_me_password(self):
        url = reverse("v2:account-check-me-password")
        resp = self.client.post(url, {"password": "Toto1234"}, format="json")
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post(url, {"password": "password"}, format="json")
        self.assertEqual(resp.status_code, 200)

    @mock.patch("django_otp.match_token")
    def test_tfa_verify_code(self, match_mock):
        user = models.User.objects.get(username="admin")
        user.totpdevice_set.create(name="Device")
        user.tfa_enabled = True
        user.save()

        url = reverse("v2:account-tfa-verify-code")
        match_mock.side_effect = [user.totpdevice_set.first()]
        data = {"code": "1234"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.json())

    def test_tfa_setup_get_qr_code(self):
        url = reverse("v2:account-tfa-setup-get-qr-code")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        user = models.User.objects.get(username="admin")
        user.totpdevice_set.create(name="Device")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/xml")

        user.tfa_enabled = True
        user.save()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    @mock.patch("django_otp.plugins.otp_totp.models.TOTPDevice.verify_token")
    def test_tfa_setup_check(self, verify_mock):
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


class AuthenticationTestCase(ModoAPITestCase):

    @mock.patch("django_otp.match_token")
    def test_2fa(self, match_mock):
        url = reverse("v2:token_obtain_pair")
        me_url = reverse("v2:account-me")
        data = {
            "username": "admin",
            "password": "password"
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer {}".format(resp.json()["access"]))
        resp = self.client.get(me_url)
        self.assertEqual(resp.status_code, 200)

        # Now we enable 2FA
        user = models.User.objects.get(username="admin")
        user.totpdevice_set.create(name="Device")
        user.tfa_enabled = True
        user.save()
        resp = self.client.get(me_url)
        self.assertEqual(resp.status_code, 418)

        # Verify code
        url = reverse("v2:account-tfa-verify-code")
        match_mock.side_effect = [user.totpdevice_set.first()]
        data = {"code": "1234"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer {}".format(resp.json()["access"]))
        resp = self.client.get(me_url)
        self.assertEqual(resp.status_code, 200)


class LanguageViewSetTestCase(ModoAPITestCase):

    def test_list(self):
        url = reverse("v2:language-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
