"""relaydomains unit tests."""

from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core.factories import UserFactory
from modoboa.lib.test_utils import MapFilesTestCaseMixin
from modoboa.lib.tests import ModoAPITestCase
from modoboa.limits import utils as limits_utils
from modoboa.transport import factories as tr_factories, models as tr_models
from . import models


class Operations:

    def _create_relay_domain(self, name, status=201, **kwargs):
        url = reverse("v2:domain-list")
        values = {
            "name": name,
            "type": "relaydomain",
            "transport": {
                "service": "relay",
                "settings": {
                    "relay_target_host": "external.host.tld",
                    "relay_target_port": 25,
                    "relay_verify_recipients": False,
                },
            },
            "enabled": True,
            "quota": 0,
            "default_mailbox_quota": 0,
        }
        values.update(kwargs)
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, status)
        return response

    def _check_limit(self, name, curvalue, maxvalue):
        limit = self.user.userobjectlimit_set.get(name=name)
        self.assertEqual(limit.current_value, curvalue)
        self.assertEqual(limit.max_value, maxvalue)


class RelayDomainsTestCase(ModoAPITestCase, Operations):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        admin_factories.populate_database()
        cls.transport = tr_factories.TransportFactory(
            pattern="relaydomain.tld",
            service="relay",
            _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": False,
            },
        )
        cls.dom = admin_factories.DomainFactory(
            name="relaydomain.tld", type="relaydomain", transport=cls.transport
        )
        admin_factories.DomainAliasFactory(name="relaydomainalias.tld", target=cls.dom)
        admin_factories.MailboxFactory(
            domain=cls.dom,
            address="local",
            user__username="local@relaydomain.tld",
            user__groups=("SimpleUsers",),
        )

    def test_domain_list(self):
        """Make sure relaydomain is listed."""
        url = reverse("v2:domain-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(len(content), 3)

    def test_create_relaydomain(self):
        """Test the creation of a relay domain.

        We also check that unique constraints are respected: domain,
        relay domain alias.

        FIXME: add a check for domain alias.
        """
        self._create_relay_domain("relaydomain1.tld")
        transport = tr_models.Transport.objects.get(pattern="relaydomain1.tld")
        self.assertEqual(transport._settings["relay_target_host"], "external.host.tld")
        self.assertEqual(transport._settings["relay_verify_recipients"], False)

        response = self._create_relay_domain("test.com", 400)
        self.assertEqual(
            response.json()["name"][0], "domain with this name already exists."
        )
        response = self._create_relay_domain("relaydomainalias.tld", 400)
        self.assertEqual(
            response.json()["name"][0],
            "domain alias with this name already exists",
        )

    def test_edit_relaydomain(self):
        """Test the modification of a relay domain.

        Rename 'relaydomain.tld' domain to 'relaydomain.org'
        """
        values = {
            "name": "relaydomain.org",
            "transport": {
                "service": "relay",
                "settings": {
                    "relay_target_host": self.transport._settings["relay_target_host"],
                    "relay_target_port": 4040,
                    "relay_verify_recipients": True,
                },
            },
            "type": "relaydomain",
            "enabled": True,
            "quota": 0,
            "default_mailbox_quota": 0,
        }
        url = reverse("v2:domain-detail", args=[self.dom.id])
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 200)
        self.transport.refresh_from_db()
        self.assertEqual(self.transport._settings["relay_target_port"], 4040)
        self.assertTrue(
            models.RecipientAccess.objects.filter(pattern=values["name"]).exists()
        )
        values["transport"]["settings"]["relay_verify_recipients"] = False
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            models.RecipientAccess.objects.filter(pattern=values["name"]).exists()
        )

    def test_relaydomain_domain_switch(self):
        """Check domain <-> relaydomain transitions."""
        domain_pk = self.dom.pk
        transport_def = {
            "service": "relay",
            "settings": {
                "relay_target_host": self.transport._settings["relay_target_host"],
                "relay_target_port": self.transport._settings["relay_target_port"],
            },
        }
        values = {
            "name": "relaydomain.tld",
            "type": "domain",
            "quota": 0,
            "default_mailbox_quota": 0,
            "enabled": True,
            "transport": transport_def,
        }
        url = reverse("v2:domain-detail", args=[domain_pk])
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["transport"][0],
            "This field is valid when type is relaydomain",
        )

        del values["transport"]
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 200)

        with self.assertRaises(tr_models.Transport.DoesNotExist):
            self.transport.refresh_from_db()
        self.dom.refresh_from_db()
        self.assertEqual(self.dom.type, "domain")
        values = {
            "name": "relaydomain.tld",
            "type": "relaydomain",
            "enabled": True,
            "quota": 0,
            "default_mailbox_quota": 0,
            "transport": transport_def,
        }
        response = self.client.put(url, values, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            admin_models.Domain.objects.get(name="relaydomain.tld").type, "relaydomain"
        )

    def test_delete_relaydomain(self):
        """Test the removal of a relay domain."""
        url = reverse("v2:domain-delete", args=[self.dom.id])
        body = {"keep_folder": False}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(tr_models.Transport.DoesNotExist):
            self.transport.refresh_from_db()

    def test_delete_recipientaccess(self):
        """Test the removal of a recipient access."""
        self.transport._settings["relay_verify_recipients"] = True
        self.transport.save()
        url = reverse("v2:domain-delete", args=[self.dom.id])
        body = {"keep_folder": False}
        response = self.client.post(url, body, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            models.RecipientAccess.objects.filter(
                pattern=self.transport.pattern
            ).exists()
        )

    def test_alias_on_relaydomain(self):
        """Create an alias on a relay domain."""
        values = {
            "address": "alias@relaydomain.tld",
            "recipients": ["recipient@relaydomain.tld"],
            "enabled": True,
        }
        url = reverse("v2:alias-list")
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            admin_models.Alias.objects.filter(address="alias@relaydomain.tld").exists()
        )
        values = {
            "address": "alias2@relaydomain.tld",
            "recipients": ["local@relaydomain.tld"],
            "enabled": True,
        }
        response = self.client.post(url, values, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            admin_models.Alias.objects.filter(address="alias2@relaydomain.tld").exists()
        )


class ImportTestCase(ModoAPITestCase):
    """Test import."""

    def test_webui_import(self):
        """Check if import from webui works."""
        f = ContentFile(
            "relaydomain;relay.com;127.0.0.1;25;relay;True;True", name="domains.csv"
        )
        url = reverse("v2:domain-import-from-csv")
        body = {"sourcefile": f}
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            admin_models.Domain.objects.filter(
                name="relay.com", type="relaydomain"
            ).exists()
        )


class LimitsTestCase(ModoAPITestCase, Operations):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        for name, _definition in limits_utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                f"deflt_user_{name}_limit", 2, app="limits"
            )
        cls.localconfig.save()
        cls.user = UserFactory.create(username="reseller", groups=("Resellers",))

    def setUp(self):
        """Initialize test."""
        super().setUp()
        self.authenticate_user(self.user)

    def test_relay_domains_limit(self):
        self._create_relay_domain("relaydomain1.tld", quota=1, default_mailbox_quota=1)
        self._check_limit("domains", 1, 2)
        self._create_relay_domain("relaydomain2.tld", quota=1, default_mailbox_quota=1)
        self._check_limit("domains", 2, 2)
        self._create_relay_domain("relaydomain3.tld", 400)
        self._check_limit("domains", 2, 2)
        domid = admin_models.Domain.objects.get(name="relaydomain2.tld").id
        url = reverse("v2:domain-delete", args=[domid])
        response = self.client.post(url, {"keep_folder": False}, format="json")
        self.assertEqual(response.status_code, 204)
        self._check_limit("domains", 1, 2)


class MapFilesTestCase(MapFilesTestCaseMixin, TestCase):
    """Test case for relaydomains."""

    MAP_FILES = ["sql-relaydomains.cf", "sql-relay-recipient-verification.cf"]
