"""Parameters API related tests."""

import httmock

from django.urls import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin.factories import populate_database
from modoboa.contacts import mocks as contact_mocks
from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase


class GlobalParametersAPITestCase(ModoAPITestCase):
    def test_applications(self):
        url = reverse("v2:parameter-global-applications")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # core, admin, limits, pdf credentials, ...
        self.assertEqual(len(resp.json()), 12)

    def test_get_structure(self):
        url = reverse("v2:parameter-global-structure")
        resp_full = self.client.get(url)
        self.assertEqual(resp_full.status_code, 200)

        resp_core = self.client.get(url + "?app=core")
        self.assertEqual(resp_core.status_code, 200)

        self.assertNotEqual(len(resp_full.json()), len(resp_core.json()))

    def test_retrieve(self):
        for app in ["core", "admin", "limits"]:
            url = reverse("v2:parameter-global-detail", args=[app])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_retrieve_hides_secrets_from_non_superadmins(self):
        """Secret global parameters must not leak to privileged non-superusers."""
        self.set_global_parameters(
            {
                "ldap_bind_password": "SECRET_BIND",
                "ldap_sync_bind_password": "SECRET_SYNC",
            },
            app="core",
        )
        url = reverse("v2:parameter-global-detail", args=["core"])

        # Superadmin keeps full read access (needed to pre-fill the admin form).
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        params = resp.json()["params"]
        self.assertEqual(params["ldap_bind_password"], "SECRET_BIND")
        self.assertEqual(params["ldap_sync_bind_password"], "SECRET_SYNC")

        # A DomainAdmin reads non-secret parameters but never the secrets.
        populate_database()
        domain_admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(domain_admin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        params = resp.json()["params"]
        self.assertNotIn("ldap_bind_password", params)
        self.assertNotIn("ldap_sync_bind_password", params)
        # Non-secret parameters are still returned.
        self.assertIn("authentication_type", params)

        # SimpleUsers remain forbidden entirely.
        simple_user = User.objects.get(username="user@test.com")
        self.authenticate_user(simple_user)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

    def test_update(self):
        data = {
            "enable_admin_limits": True,
            "deflt_user_domain_admins_limit": 0,
            "deflt_user_domains_limit": 0,
            "deflt_user_domain_aliases_limit": 0,
            "deflt_user_mailboxes_limit": 0,
            "deflt_user_mailbox_aliases_limit": 0,
            "deflt_user_quota_limit": 0,
            "enable_domain_limits": False,
            "deflt_domain_domain_admins_limit": 0,
            "deflt_domain_domain_aliases_limit": 0,
            "deflt_domain_mailboxes_limit": 0,
            "deflt_domain_mailbox_aliases_limit": 0,
        }
        url = reverse("v2:parameter-global-detail", args=["limits"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_update_admin_settings(self):
        data = {
            "default_domain_quota": -1,
            "default_mailbox_quota": -1,
            "valid_mxs": "mail.test.com",
            "custom_dns_server": "",
            "dkim_keys_storage_dir": "/wrong",
        }
        url = reverse("v2:parameter-global-detail", args=["admin"])
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        errors = resp.json()
        self.assertEqual(
            errors["valid_mxs"],
            ["This field only allows valid IP addresses (or networks)"],
        )
        self.assertEqual(errors["default_domain_quota"], ["Must be a positive integer"])
        self.assertEqual(
            errors["default_mailbox_quota"], ["Must be a positive integer"]
        )

        data = {
            "enable_mx_checks": True,
            "domains_must_have_authorized_mx": True,
            "valid_mxs": "",
            "custom_dns_server": "",
            "dkim_keys_storage_dir": "",
        }
        resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json()["valid_mxs"],
            ["Define at least one authorized network / address"],
        )


class UserParametersAPITestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        populate_database()
        cls.user = User.objects.get(username="admin@test.com")
        cls.da_token = Token.objects.create(user=cls.user)

    def setUp(self):
        super().setUp()
        self.set_global_parameter(
            "server_location", "http://localhost:5232", app="calendars"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.da_token.key)

    def test_applications(self):
        url = reverse("v2:parameter-user-applications")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)

    def test_get_structure(self):
        url = reverse("v2:parameter-user-structure")
        resp_full = self.client.get(url)
        self.assertEqual(resp_full.status_code, 200)

        resp_contacts = self.client.get(url + "?app=contacts")
        self.assertEqual(resp_contacts.status_code, 200)

        # Only 1 section for contacts
        self.assertEqual(len(resp_contacts.json()), 1)

    def test_retrieve(self):
        for app in ["contacts", "webmail"]:
            url = reverse("v2:parameter-user-detail", args=[app])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_update(self):
        data = {"enable_carddav_sync": True, "sync_frequency": 300}
        url = reverse("v2:parameter-user-detail", args=["contacts"])
        with httmock.HTTMock(contact_mocks.options_mock, contact_mocks.mkcol_mock):
            resp = self.client.put(url, data, format="json")
        self.assertEqual(resp.status_code, 200)
