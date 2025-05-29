"""Testing utilities."""

import socket
import tempfile

from django.conf import settings
from django.core import management
from django.test import TestCase

from importlib import import_module

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from modoboa.core import models as core_models
from .. import sysutils

try:
    s = socket.create_connection(("127.0.0.1", 25))
    s.close()
    NO_SMTP = False
except OSError:
    NO_SMTP = True

try:
    import ldap  # noqa

    NO_LDAP = False
except ImportError:
    NO_LDAP = True


SETTINGS_SAMPLE = {
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
    "limits-deflt_domain_domain_admins_limit": "0",
    "limits-enable_admin_limits": "True",
    "core-ldap_bind_dn": "",
    "core-enable_api_communication": "True",
    "limits-deflt_user_domain_admins_limit": "0",
    "limits-enable_domain_limits": "False",
    "csrfmiddlewaretoken": "SGgMVZsA4TPqoiV786TMST6xgOlhAf4F",
    "limits-deflt_user_mailboxes_limit": "0",
    "core-password_scheme": "plain",
    "core-update_scheme": True,
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
    "admin-enable_ipv6_mx_checks": "True",
    "core-ldap_search_base": "",
    "admin-valid_mxs": "",
    "limits-deflt_user_domains_limit": "0",
    "core-ldap_search_filter": "(mail=%(user)s)",
    "core-ldap_secured": "none",
    "core-ldap_user_dn_template": "",
    "core-default_password": "Toto1000",
    "limits-deflt_user_quota_limit": "0",
    "core-hide_features_widget": "False",
    "core-enable_inactive_accounts": "True",
    "core-inactive_account_threshold": "30",
    "admin-domains_must_have_authorized_mx": False,
    "core-random_password_length": "8",
    "admin-create_alias_on_mbox_rename": False,
    "admin-dkim_keys_storage_dir": "",
    "admin-dkim_default_key_length": 1024,
    "admin-custom_dns_server": "193.43.55.67",
    "admin-enable_spf_checks": True,
    "admin-enable_dkim_checks": True,
    "admin-enable_dmarc_checks": True,
    "admin-enable_autoconfig_checks": True,
    "core-ldap_enable_sync": False,
    "core-ldap_sync_bind_dn": "",
    "core-ldap_sync_bind_password": "",
    "core-ldap_sync_account_dn_template": "",
    "core-ldap_sync_delete_remote_account": False,
    "core-send_new_versions_email": False,
    "core-new_versions_email_rcpt": "postmaster@domain.test",
    "core-ldap_enable_secondary_server": False,
    "core-ldap_secondary_server_address": "localhost",
    "core-ldap_secondary_server_port": 389,
    "core-ldap_enable_import": False,
    "core-ldap_import_search_base": "",
    "core-ldap_import_search_filter": "",
    "core-ldap_import_username_attr": "cn",
    "core-sms_password_recovery": False,
    "core-sms_provider": "",
    "core-sms_ovh_endpoint": "ovh-eu",
    "core-password_recovery_msg": "",
    "core-ldap_dovecot_sync": False,
    "maillog-logfile": "/var/log/mail.log",
    "maillog-rrd_rootdir": "/tmp",
    "maillog-greylist": False,
    "pdfcredentials-enabled_pdfcredentials": True,
    "pdfcredentials-storage_dir": "./",
    "pdfcredentials-delete_first_dl": True,
    "pdfcredentials-generate_at_creation": True,
    "pdfcredentials-title": "Modoboa",
    "pdfcredentials-webpanel_url": "local.host/",
    "pdfcredentials-custom_message": "test",
    "pdfcredentials-include_connection_settings": False,
    "pdfcredentials-smtp_server_address": "127.0.0.1",
    "pdfcredentials-smtp_server_port": 666,
    "pdfcredentials-smtp_connection_security": "starttls",
    "pdfcredentials-imap_server_address": "127.0.0.1",
    "pdfcredentials-imap_server_port": 667,
    "pdfcredentials-imap_connection_security": "starttls",
    "dmarc-enable_rlookups": False,
    "imap_migration-enabled_imapmigration": True,
    "imap_migration-max_sync_accounts": 2,
    "imap_migration-create_folders": True,
    "postfix_autoreply-autoreplies_timeout": 86400,
    "postfix_autoreply-default_subject": "I'm off",
    "postfix_autoreply-default_content": "I'm off",
    "sievefilters-server": "127.0.0.1",
    "sievefilters-port": 4190,
    "sievefilters-starttls": False,
    "sievefilters-authentication_mech": "AUTO",
    "sievefilters-imap_server": "127.0.0.1",
    "sievefilters-imap_secured": False,
    "sievefilters-imap_port": 143,
}


class ParametersMixin:
    """Add tools to manage parameters."""

    @classmethod
    def setUpTestData(cls):  # noqa
        """Set LocalConfig instance."""
        super().setUpTestData()
        cls.localconfig = core_models.LocalConfig.objects.first()

    def set_global_parameter(self, name, value, app=None):
        """Set global parameter for the given app."""
        if app is None:
            app = sysutils.guess_extension_name()
        self.localconfig.parameters.set_value(name, value, app=app)
        self.localconfig.save()

    def set_global_parameters(self, parameters, app=None):
        """Set/update global parameters for the given app."""
        if app is None:
            app = sysutils.guess_extension_name()
        self.localconfig.parameters.set_values(parameters, app=app)
        self.localconfig.save()


class SimpleModoTestCase(ParametersMixin, TestCase):
    """Simple class to add parameters editing."""


class ModoTestCase(ParametersMixin, TestCase):
    """All test cases must inherit from this one."""

    @classmethod
    def setUpTestData(cls):  # noqa
        """Create a default user."""
        super().setUpTestData()
        management.call_command("load_initial_data", "--no-frontend")

    def setUp(self, username="admin", password="password"):
        """Initiate test context."""
        self.assertEqual(self.client.login(username=username, password=password), True)
        self.workdir = tempfile.mkdtemp()
        self.set_global_parameter("storage_dir", self.workdir, app="pdfcredentials")

    def ajax_request(self, method, url, params=None, status=200):
        if params is None:
            params = {}
        response = getattr(self.client, method)(
            url, params, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, status)
        return response.json()

    def ajax_post(self, *args, **kwargs):
        return self.ajax_request("post", *args, **kwargs)

    def ajax_put(self, *args, **kwargs):
        return self.ajax_request("put", *args, **kwargs)

    def ajax_delete(self, *args, **kwargs):
        return self.ajax_request("delete", *args, **kwargs)

    def ajax_get(self, *args, **kwargs):
        return self.ajax_request("get", *args, **kwargs)


class ModoAPITestCase(ParametersMixin, APITestCase):
    """All test cases must inherit from this one."""

    @classmethod
    def setUpTestData(cls):  # noqa
        """Create a default user."""
        super().setUpTestData()
        management.call_command("load_initial_data")
        cls.sadmin = core_models.User.objects.get(username="admin")
        cls.token = Token.objects.create(user=cls.sadmin)

    def setUp(self):
        """Setup."""
        super().setUp()
        self._tokens = {self.sadmin: self.token}
        self.authenticate_user(self.sadmin)
        self.workdir = tempfile.mkdtemp()
        self.set_global_parameter("storage_dir", self.workdir, app="pdfcredentials")

    def authenticate_user(self, user: core_models.User) -> Token:
        if user not in self._tokens:
            self._tokens[user] = Token.objects.create(user=user)

        token = self._tokens[user]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def create_session(self):
        """Enable session storage across requests."""
        session_engine = import_module(settings.SESSION_ENGINE)
        store = session_engine.SessionStore()
        store.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
