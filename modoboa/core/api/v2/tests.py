"""Core API related tests."""

import copy

from django.urls import reverse

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
    "default_top_redirection": ""
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
