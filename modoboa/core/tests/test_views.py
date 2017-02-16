"""Core views test cases."""

import json

from testfixtures import compare

from django import forms
from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase
from modoboa.parameters import forms as param_forms
from modoboa.parameters import tools as param_tools

from .. import factories
from .. import models
from .. import signals


def announcement(sender, location, **kwargs):
    """Simpler handler."""
    return "This is an annoucement!"


class LoginTestCase(ModoTestCase):
    """Login page test cases."""

    def test_announcements(self):
        """Check if announcements are displayed."""
        signals.get_announcements.connect(announcement)
        response = self.client.get(reverse("core:login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("This is an annoucement!", response.content)


class DashboardTestCase(ModoTestCase):
    """Dashboard tests."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        super(DashboardTestCase, cls).setUpTestData()
        cls.dadmin = factories.UserFactory(
            username="admin@test.com", groups=("DomainAdmins",)
        )
        cls.user = factories.UserFactory(
            username="user@test.com", groups=("SimpleUsers",)
        )

    def test_access(self):
        """Load dashboard."""
        url = reverse("core:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Latest news", response.content)
        self.client.logout()
        self.client.login(username=self.dadmin.username, password="toto")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Latest news", response.content)
        self.client.logout()
        self.client.login(username=self.user.username, password="toto")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_root_dispatch(self):
        """Check root dispatching."""
        url = reverse("core:root")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse("core:dashboard")))

    def test_top_notifications(self):
        """Check top notifications service."""
        url = reverse("core:top_notifications_check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)


class SettingsTestCase(ModoTestCase):
    """Settings tests."""

    settings_sample = {
        "core-check_new_versions": "True",
        "core-log_maximum_age": "365",
        "core-ldap_auth_method": "searchbind",
        "limits-deflt_domain_mailbox_aliases_limit": "0",
        "core-send_statistics": "True",
        "core-default_top_redirection": "user",
        "core-sender_address": "noreply@modoboa.org",
        "admin-auto_account_removal": "False",
        "core-ldap_server_port": "389",
        "core-rounds_number": "70000",
        "core-ldap_bind_password": "",
        "limits-deflt_domain_domain_aliases_limit": "0",
        "core-secret_key": ":?j3]QPWo!.'_c4n",
        "relaydomains-master_cf_path": "/etc/postfix/master.cf",
        "limits-deflt_domain_domain_admins_limit": "0",
        "limits-enable_admin_limits": "True",
        "core-ldap_bind_dn": "",
        "core-enable_api_communication": "True",
        "limits-deflt_user_domain_admins_limit": "0",
        "limits-enable_domain_limits": "False",
        "csrfmiddlewaretoken": "SGgMVZsA4TPqoiV786TMST6xgOlhAf4F",
        "limits-deflt_user_mailboxes_limit": "0",
        "core-password_scheme": "sha512crypt",
        "core-items_per_page": "30",
        "limits-deflt_user_mailbox_aliases_limit": "0",
        "limits-deflt_domain_mailboxes_limit": "0",
        "core-ldap_is_active_directory": "False",
        "core-ldap_group_type": "posixgroup",
        "limits-deflt_user_domain_aliases_limit": "0",
        "core-top_notifications_check_interval": "30",
        "core-ldap_password_attribute": "userPassword",
        "admin-auto_create_domain_and_mailbox": "True",
        "admin-enable_dnsbl_checks": "True",
        "admin-default_domain_quota": "0",
        "admin-default_mailbox_quota": "0",
        "core-ldap_server_address": "localhost",
        "core-authentication_type": "local",
        "core-ldap_admin_groups": "",
        "core-ldap_groups_search_base": "",
        "admin-enable_mx_checks": "True",
        "core-ldap_search_base": "",
        "admin-valid_mxs": "",
        "limits-deflt_user_domains_limit": "0",
        "core-ldap_search_filter": "(mail=%(user)s)",
        "core-ldap_secured": "False",
        "core-ldap_user_dn_template": "",
        "core-default_password": "Toto1000",
        "limits-deflt_user_quota_limit": "0",
    }

    def test_get_settings(self):
        """Test settings display."""
        url = reverse("core:parameters")
        response = self.ajax_get(url)
        for app in ["core", "admin", "limits", "relaydomains"]:
            self.assertIn('data-app="{}"'.format(app), response["content"])

    def test_save_settings(self):
        """Test settings save."""
        url = reverse("core:parameters")
        response = self.client.post(url, self.settings_sample, format="json")
        self.assertEqual(response.status_code, 200)
        self.settings_sample["core-rounds_number"] = ""
        response = self.client.post(url, self.settings_sample, format="json")
        self.assertEqual(response.status_code, 400)
        compare(response.json(), {
            "form_errors": {"rounds_number": ["This field is required."]},
            "prefix": "core"
        })


class UserSettings(param_forms.UserParametersForm):
    """Stupid user settings form."""

    app = "core"

    test = forms.CharField()


def extra_user_menu(sender, location, user, **kwargs):
    """Return extra menu entry."""
    return [
        {"name": "test_menu_entry",
         "class": "ajaxnav",
         "url": "toto/",
         "label": "Test"}
    ]


class PreferencesTestCase(ModoTestCase):
    """Test user preferences."""

    @classmethod
    def setUpClass(cls):
        """Register user form."""
        super(PreferencesTestCase, cls).setUpClass()
        param_tools.registry.add("user", UserSettings, "Test")

    @classmethod
    def tearDownClass(cls):
        """Remove user class."""
        super(PreferencesTestCase, cls).tearDownClass()
        del param_tools.registry._registry["user"]["core"]

    def test_get_user_index(self):
        """Retrieve index page."""
        signals.extra_user_menu_entries.connect(extra_user_menu)
        url = reverse("core:user_index")
        response = self.client.get(url)
        self.assertContains(response, 'name="test_menu_entry"')

    def test_get_preferences(self):
        """Test preferences display."""
        url = reverse("core:user_preferences")
        self.ajax_get(url)

    def test_save_preferences(self):
        """Test preferences save."""
        url = reverse("core:user_preferences")
        response = self.client.post(url, {"core-test": "toto"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "Preferences saved")

        admin = models.User.objects.get(username="admin")
        self.assertEqual(admin.parameters.get_value("test"), "toto")
