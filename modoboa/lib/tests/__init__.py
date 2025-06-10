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
    "core": {
        "check_new_versions": "True",
        "log_maximum_age": "365",
        "ldap_auth_method": "searchbind",
        "send_statistics": "True",
        "default_top_redirection": "user",
        "sender_address": "noreply@modoboa.org",
        "ldap_server_port": "389",
        "rounds_number": "70000",
        "ldap_bind_password": "",
        "secret_key": ":?j3]QPWo!.'_c4n",
        "ldap_bind_dn": "",
        "enable_api_communication": "True",
        "password_scheme": "plain",
        "update_scheme": True,
        "items_per_page": "30",
        "ldap_is_active_directory": "False",
        "ldap_group_type": "posixgroup",
        "top_notifications_check_interval": "30",
        "ldap_password_attribute": "userPassword",
        "ldap_server_address": "localhost",
        "authentication_type": "local",
        "ldap_admin_groups": "",
        "ldap_groups_search_base": "",
        "ldap_search_base": "",
        "ldap_enable_sync": False,
        "ldap_sync_bind_dn": "",
        "ldap_sync_bind_password": "",
        "ldap_sync_account_dn_template": "",
        "ldap_sync_delete_remote_account": False,
        "send_new_versions_email": False,
        "new_versions_email_rcpt": "postmaster@domain.test",
        "ldap_enable_secondary_server": False,
        "ldap_secondary_server_address": "localhost",
        "ldap_secondary_server_port": 389,
        "ldap_enable_import": False,
        "ldap_import_search_base": "",
        "ldap_import_username_attr": "cn",
        "sms_password_recovery": False,
        "sms_provider": "",
        "sms_ovh_endpoint": "ovh-eu",
        "password_recovery_msg": "",
        "ldap_dovecot_sync": False,
        "hide_features_widget": "False",
        "enable_inactive_accounts": "True",
        "inactive_account_threshold": "30",
        "ldap_search_filter": "(mail=%(user)s)",
        "ldap_secured": "none",
        "ldap_user_dn_template": "",
        "default_password": "Toto1000",
        "random_password_length": "8",
    },
    "limits": {
        "deflt_domain_mailbox_aliases_limit": "0",
        "deflt_domain_domain_aliases_limit": "0",
        "deflt_domain_domain_admins_limit": "0",
        "enable_domain_limits": "False",
        "enable_admin_limits": "True",
        "deflt_user_domain_admins_limit": "0",
        "deflt_user_mailboxes_limit": "0",
        "deflt_user_mailbox_aliases_limit": "0",
        "deflt_domain_mailboxes_limit": "0",
        "deflt_user_domain_aliases_limit": "0",
        "deflt_user_domains_limit": "0",
        "deflt_user_quota_limit": "0",
    },
    "admin": {
        "auto_account_removal": "False",
        "auto_create_domain_and_mailbox": "True",
        "enable_dnsbl_checks": "True",
        "default_domain_quota": "0",
        "default_mailbox_quota": "0",
        "enable_mx_checks": "True",
        "enable_ipv6_mx_checks": "True",
        "create_alias_on_mbox_rename": False,
        "dkim_keys_storage_dir": "",
        "dkim_default_key_length": 1024,
        "custom_dns_server": "193.43.55.67",
        "enable_spf_checks": True,
        "enable_dkim_checks": True,
        "enable_dmarc_checks": True,
        "enable_autoconfig_checks": True,
        "valid_mxs": "",
        "domains_must_have_authorized_mx": False,
    },
    "maillog": {
        "logfile": "/var/log/mail.log",
        "rrd_rootdir": "/tmp",
        "greylist": False,
    },
    "pdfcredentials": {
        "enabled_pdfcredentials": True,
        "storage_dir": "./",
        "delete_first_dl": True,
        "generate_at_creation": True,
        "title": "Modoboa",
        "webpanel_url": "local.host/",
        "custom_message": "test",
        "include_connection_settings": False,
        "smtp_server_address": "127.0.0.1",
        "smtp_server_port": 666,
        "smtp_connection_security": "starttls",
        "imap_server_address": "127.0.0.1",
        "imap_server_port": 667,
        "imap_connection_security": "starttls",
    },
    "dmarc": {
        "enable_rlookups": False,
    },
    "imap_migration": {
        "enabled_imapmigration": True,
        "max_sync_accounts": 2,
        "create_folders": True,
    },
    "autoreply": {
        "autoreplies_timeout": 86400,
        "default_subject": "I'm off",
        "default_content": "I'm off",
    },
    "sievefilters": {
        "server": "127.0.0.1",
        "port": 4190,
        "starttls": False,
        "authentication_mech": "AUTO",
        "imap_server": "127.0.0.1",
        "imap_secured": False,
        "imap_port": 143,
    },
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

    pass


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
        management.call_command("load_initial_data", "--no-frontend")
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
