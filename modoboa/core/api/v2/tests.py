"""Core API related tests."""

import copy
import getpass
import io
import shutil
import tempfile
from unittest import mock

from PIL import Image

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, tag
from django.urls import reverse

from modoboa.admin import (
    factories,
    models as admin_models,
    constants as admin_constants,
)
from modoboa.core import factories as core_factories
from modoboa.core import models, constants, signals
from modoboa.core.tests import utils
from modoboa.lib.tests import ModoAPITestCase
from modoboa.parameters import tools as param_tools

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
    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_me(self):
        url = reverse("v2:account-me")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        me = resp.json()
        self.assertEqual(me["username"], "admin")

    def test_update_me(self):
        url = reverse("v2:account-me")
        data = {
            "first_name": "First name",
            "secondary_email": "toto@iti.com",
            "language": "fr",
        }
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        me = resp.json()
        self.assertEqual(me["secondary_email"], data["secondary_email"])

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

    def test_available_applications(self):
        url = reverse("v2:account-available-applications")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # admin -> only 2 apps.
        self.assertEqual(len(resp.json()), 2)

        # Domain admin with mailbox
        dadmin = models.User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 5)

        # Simple user
        user = models.User.objects.get(username="user@test.com")
        self.authenticate_user(user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 4)

    @override_settings(
        MODOBOA_APPS=[
            "modoboa",
            "modoboa.core",
            "modoboa.lib",
            "modoboa.admin",
            "modoboa.transport",
            "modoboa.relaydomains",
            "modoboa.limits",
            "modoboa.parameters",
            "modoboa.dnstools",
            "modoboa.policyd",
            "modoboa.maillog",
            "modoboa.pdfcredentials",
            "modoboa.dmarc",
            "modoboa.imap_migration",
            "modoboa.autoreply",
            "modoboa.sievefilters",
            "modoboa.rspamd",
        ]
    )
    def test_available_applications_with_disabled(self):
        url = reverse("v2:account-available-applications")
        # Domain admin with mailbox
        dadmin = models.User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)


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


class ThemeAPITestCase(ModoAPITestCase):
    def test_get(self):
        url = reverse("v2:theme")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        theme = response.json()
        self.assertEqual(theme["theme_primary_color"], "#046BF8")
        # Logo URL fields default to empty so the frontend / auth template
        # fall back to the bundled defaults.
        self.assertEqual(theme["theme_login_logo_url"], "")
        self.assertEqual(theme["theme_menu_logo_url"], "")
        self.assertEqual(theme["theme_creation_form_logo_url"], "")

        self.set_global_parameter("theme_primary_color", "#FF0000")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        theme = response.json()
        self.assertEqual(theme["theme_primary_color"], "#FF0000")

    def test_get_theme_parameters_signal(self):
        """Plugin receivers can override theme colors via the signal."""
        received = {}

        def handler(sender, current_values, **kwargs):
            received["current_values"] = dict(current_values)
            return {"theme_primary_color": "#123456"}

        signals.get_theme_parameters.connect(handler)
        try:
            url = reverse("v2:theme")
            response = self.client.get(url)
        finally:
            signals.get_theme_parameters.disconnect(handler)

        self.assertEqual(response.status_code, 200)
        theme = response.json()
        self.assertEqual(theme["theme_primary_color"], "#123456")
        # Non-overridden keys keep their stored value.
        self.assertEqual(theme["theme_secondary_color"], "#F18429")
        # Receiver was passed the pre-override values as current_values.
        self.assertEqual(received["current_values"]["theme_primary_color"], "#046BF8")


class ThemeLogoUploadAPITestCase(ModoAPITestCase):
    """Tests for POST/DELETE on /api/v2/theme/logo/."""

    def setUp(self):
        super().setUp()
        # Isolate file writes from the real MEDIA_ROOT.
        media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media_root, ignore_errors=True)
        media_override = override_settings(MEDIA_ROOT=media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)

    @staticmethod
    def _png_file(name="logo.png"):
        buf = io.BytesIO()
        Image.new("RGB", (1, 1), (255, 0, 0)).save(buf, format="PNG")
        return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")

    def _get_param(self, logo_type):
        return param_tools.get_global_parameter(
            f"theme_{logo_type}_logo_url", app="core"
        )

    def test_upload_saves_param_and_returns_url(self):
        url = reverse("v2:theme-logo-upload")
        response = self.client.post(
            url,
            {"logo_type": "menu", "image": self._png_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["logo_type"], "menu")
        self.assertTrue(body["url"].startswith("/media/theme_logos/menu_"))
        self.assertEqual(self._get_param("menu"), body["url"])

    def test_upload_supports_each_logo_type(self):
        url = reverse("v2:theme-logo-upload")
        for logo_type in ("login", "menu", "creation_form"):
            with self.subTest(logo_type=logo_type):
                response = self.client.post(
                    url,
                    {"logo_type": logo_type, "image": self._png_file()},
                    format="multipart",
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["logo_type"], logo_type)
                self.assertTrue(self._get_param(logo_type))

    def test_upload_rejects_invalid_logo_type(self):
        url = reverse("v2:theme-logo-upload")
        response = self.client.post(
            url,
            {"logo_type": "header", "image": self._png_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_non_image_file(self):
        url = reverse("v2:theme-logo-upload")
        response = self.client.post(
            url,
            {
                "logo_type": "menu",
                "image": SimpleUploadedFile(
                    "evil.txt", b"not an image", content_type="text/plain"
                ),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_clear_resets_param(self):
        self.set_global_parameter(
            "theme_menu_logo_url", "/media/theme_logos/old.png", app="core"
        )
        url = reverse("v2:theme-logo-upload")
        response = self.client.delete(f"{url}?logo_type=menu")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self._get_param("menu"), "")

    def test_clear_rejects_invalid_logo_type(self):
        url = reverse("v2:theme-logo-upload")
        response = self.client.delete(f"{url}?logo_type=header")
        self.assertEqual(response.status_code, 400)

    def test_clear_rejects_missing_logo_type(self):
        url = reverse("v2:theme-logo-upload")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)

    def test_endpoint_requires_superuser(self):
        # Authenticated regular user — IsSuperUser should reject both verbs.
        regular = core_factories.UserFactory(username="user@test.com")
        self.authenticate_user(regular)
        url = reverse("v2:theme-logo-upload")

        with self.subTest(method="POST"):
            response = self.client.post(
                url,
                {"logo_type": "menu", "image": self._png_file()},
                format="multipart",
            )
            self.assertEqual(response.status_code, 403)

        with self.subTest(method="DELETE"):
            response = self.client.delete(f"{url}?logo_type=menu")
            self.assertEqual(response.status_code, 403)


class NewsFeedAPIViewTestCase(ModoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    @tag("network")
    def test_get(self):
        url = reverse("v2:news-feed")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)

    @override_settings(DISABLE_DASHBOARD_EXTERNAL_QUERIES=True)
    def test_if_disabling_from_settings_works(self):
        url = reverse("v2:news-feed")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

    @tag("network")
    def test_custom_rss_feed(self):
        self.set_global_parameter(
            "rss_feed_url", "https://www.djangoproject.com/rss/weblog/"
        )
        # Try as superadmin
        url = reverse("v2:news-feed")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("modoboa", response.json()[0]["link"])

        # Try as superadmin and show_rss_feed_to_superadmins enabled
        self.set_global_parameter("show_rss_feed_to_superadmins", True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("django", response.json()[0]["link"])

        # Try as domainadmin
        dadmin = models.User.objects.get(username="admin@test.com")
        self.authenticate_user(dadmin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("django", response.json()[0]["link"])

        # Try fallback
        self.set_global_parameter("rss_feed_url", "")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("modoboa", response.json()[0]["link"])


class StatisticsAPIViewTestCase(ModoAPITestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_get_statistics(self):
        url = reverse("v2:statistics")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertEqual(stats["domain_count"], 2)
        self.assertEqual(stats["account_count"], 5)
        self.assertEqual(stats["alias_count"], 3)


class SchemaDocumentationTestCase(ModoAPITestCase):
    """Tests for the schema documentation endpoints."""

    def test_swagger_view_does_not_crash(self):
        """The swagger UI must render without an AttributeError.

        Regression test for #4102: using a permission class
        (AllowAny) in SERVE_AUTHENTICATION caused drf-spectacular to
        call ``.authenticate()`` on an object that doesn't have it.
        Fix: use SERVE_PERMISSIONS instead of SERVE_AUTHENTICATION.
        """
        url = reverse("docs-index-v2")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_schema_json_view(self):
        """The JSON schema view must return a valid response."""
        url = reverse("schema-v2")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
