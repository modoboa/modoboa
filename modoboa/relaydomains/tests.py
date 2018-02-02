# -*- coding: utf-8 -*-

"""relaydomains unit tests."""

from __future__ import unicode_literals

import json

from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core.factories import UserFactory
from modoboa.lib.test_utils import MapFilesTestCaseMixin
from modoboa.lib.tests import ModoAPITestCase, ModoTestCase
from modoboa.limits import utils as limits_utils
from modoboa.transport import factories as tr_factories, models as tr_models
from . import models


class Operations(object):

    def _create_relay_domain(self, name, status=200, **kwargs):
        values = {
            "name": name,
            "create_dom_admin": False,
            "type": "relaydomain",
            "service": "relay",
            "relay_target_host": "external.host.tld",
            "relay_target_port": 25,
            "enabled": True,
            "stepid": "step3",
            "quota": 0,
            "default_mailbox_quota": 0
        }
        values.update(kwargs)
        return self.ajax_post(
            reverse("admin:domain_add"),
            values, status
        )

    def _relay_domain_alias_operation(self, optype, domain, name, status=200):
        transport = tr_models.Transport.objects.get(pattern=domain.name)
        values = {
            "name": domain.name,
            "service": "relay",
            "relay_target_host": transport._settings["relay_target_host"],
            "relay_target_port": transport._settings["relay_target_port"],
            "type": "relaydomain",
            "quota": domain.quota,
            "default_mailbox_quota": domain.default_mailbox_quota
        }
        aliases = [alias.name for alias in domain.domainalias_set.all()]
        if optype == "add":
            aliases.append(name)
        else:
            aliases.remove(name)
        for cpt, alias in enumerate(aliases):
            fname = "aliases" if not cpt else "aliases_%d" % cpt
            values[fname] = alias
        return self.ajax_post(
            reverse("admin:domain_change",
                    args=[domain.id]),
            values, status
        )

    def _check_limit(self, name, curvalue, maxvalue):
        limit = self.user.userobjectlimit_set.get(name=name)
        self.assertEqual(limit.current_value, curvalue)
        self.assertEqual(limit.max_value, maxvalue)


class RelayDomainsTestCase(ModoTestCase, Operations):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(RelayDomainsTestCase, cls).setUpTestData()
        admin_factories.populate_database()
        cls.transport = tr_factories.TransportFactory(
            pattern="relaydomain.tld", service="relay",
            _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": "25",
                "relay_verify_recipients": False
            }
        )
        cls.dom = admin_factories.DomainFactory(
            name="relaydomain.tld", type="relaydomain",
            transport=cls.transport)
        admin_factories.DomainAliasFactory(
            name="relaydomainalias.tld", target=cls.dom)
        admin_factories.MailboxFactory(
            domain=cls.dom, address="local",
            user__username="local@relaydomain.tld",
            user__groups=("SimpleUsers", )
        )

    def test_domain_list_view(self):
        """Make sure relaydomain is listed."""
        url = reverse("admin:_domain_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("relaydomain.tld", content["rows"])
        self.assertIn("Relay domain", content["rows"])

    def test_create_relaydomain(self):
        """Test the creation of a relay domain.

        We also check that unique constraints are respected: domain,
        relay domain alias.

        FIXME: add a check for domain alias.
        """
        self._create_relay_domain("relaydomain1.tld")
        transport = tr_models.Transport.objects.get(pattern="relaydomain1.tld")
        self.assertEqual(
            transport._settings["relay_target_host"], "external.host.tld")
        self.assertEqual(
            transport._settings["relay_verify_recipients"], False)

        resp = self._create_relay_domain("test.com", 400)
        self.assertEqual(resp["form_errors"]["name"][0],
                         "Domain with this Name already exists.")
        resp = self._create_relay_domain("relaydomainalias.tld", 400)
        self.assertEqual(
            resp["form_errors"]["name"][0],
            "A domain alias with this name already exists"
        )

    def test_create_relaydomainalias(self):
        """Test the creation of a relay domain alias.

        We also check that unique constraints are respected: domain,
        relay domain.

        FIXME: add a check for domain alias.
        """
        self._relay_domain_alias_operation(
            "add", self.dom, "relaydomainalias1.tld"
        )
        resp = self._relay_domain_alias_operation(
            "add", self.dom, "test.com", 400
        )
        self.assertEqual(
            resp["form_errors"]["aliases_2"][0],
            "A domain with this name already exists"
        )
        resp = self._relay_domain_alias_operation(
            "add", self.dom, self.dom.name, 400
        )
        self.assertEqual(
            resp["form_errors"]["aliases_2"][0],
            "A domain with this name already exists"
        )

    def test_edit_relaydomain(self):
        """Test the modification of a relay domain.

        Rename 'relaydomain.tld' domain to 'relaydomain.org'
        """
        values = {
            "name": "relaydomain.org",
            "service": "relay",
            "relay_target_host": self.transport._settings["relay_target_host"],
            "relay_target_port": 4040,
            "relay_verify_recipients": True,
            "type": "relaydomain",
            "enabled": True,
            "quota": 0, "default_mailbox_quota": 0
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[self.dom.id]),
            values
        )
        self.transport.refresh_from_db()
        self.assertEqual(
            self.transport._settings["relay_target_port"], 4040)
        self.assertTrue(
            models.RecipientAccess.objects.filter(
                pattern=values["name"]).exists())
        values["relay_verify_recipients"] = False
        self.ajax_post(
            reverse("admin:domain_change", args=[self.dom.id]),
            values
        )
        self.assertFalse(
            models.RecipientAccess.objects.filter(
                pattern=values["name"]).exists())

    def test_relaydomain_domain_switch(self):
        """Check domain <-> relaydomain transitions."""
        domain_pk = self.dom.pk
        values = {
            "name": "relaydomain.tld",
            "type": "domain",
            "quota": 0,
            "default_mailbox_quota": 0,
            "enabled": True,
            "service": "relay",
            "relay_target_host": self.transport._settings["relay_target_host"],
            "relay_target_port": self.transport._settings["relay_target_port"]
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain_pk]), values)
        with self.assertRaises(tr_models.Transport.DoesNotExist):
            self.transport.refresh_from_db()
        self.dom.refresh_from_db()
        self.assertEqual(self.dom.type, "domain")
        values = {
            "name": "relaydomain.tld",
            "type": "relaydomain",
            "enabled": True,
            "quota": 0,
            "default_mailbox_quota": 0
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain_pk]), values)
        self.assertEqual(
            admin_models.Domain.objects.get(name="relaydomain.tld").type,
            "relaydomain")

    def test_edit_relaydomainalias(self):
        """Test the modification of a relay domain alias.

        Rename 'relaydomainalias.tld' domain to 'relaydomainalias.net'
        """
        values = {
            "name": "relaydomain.org",
            "service": "relay",
            "relay_target_host": self.transport._settings["relay_target_host"],
            "relay_target_port": self.transport._settings["relay_target_port"],
            "type": "relaydomain",
            "aliases": "relaydomainalias.net",
            "quota": 0, "default_mailbox_quota": 0
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[self.dom.id]),
            values
        )
        admin_models.DomainAlias.objects.get(name="relaydomainalias.net")
        with self.assertRaises(admin_models.DomainAlias.DoesNotExist):
            admin_models.DomainAlias.objects.get(name="relaydomainalias.tld")

    def test_delete_relaydomain(self):
        """Test the removal of a relay domain."""
        self.ajax_post(
            reverse("admin:domain_delete", args=[self.dom.id]),
            {}
        )
        with self.assertRaises(tr_models.Transport.DoesNotExist):
            self.transport.refresh_from_db()

    def test_delete_recipientaccess(self):
        """Test the removal of a recipient access."""
        self.transport._settings["relay_verify_recipients"] = True
        self.transport.save()
        self.ajax_post(
            reverse("admin:domain_delete", args=[self.dom.id]),
            {}
        )
        self.assertFalse(
            models.RecipientAccess.objects.filter(
                pattern=self.transport.pattern).exists())

    def test_alias_on_relaydomain(self):
        """Create an alias on a relay domain."""
        values = {
            "address": "alias@relaydomain.tld",
            "recipients": "recipient@relaydomain.tld",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertTrue(
            admin_models.Alias.objects.filter(
                address="alias@relaydomain.tld").exists())
        values = {
            "address": "alias2@relaydomain.tld",
            "recipients": "local@relaydomain.tld",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        self.assertTrue(
            admin_models.Alias.objects.filter(
                address="alias2@relaydomain.tld").exists())


class ImportTestCase(ModoTestCase):
    """Test import."""

    def test_webui_import(self):
        """Check if import from webui works."""
        f = ContentFile("relaydomain;relay.com;127.0.0.1;25;relay;True;True",
                        name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(
            admin_models.Domain.objects.filter(
                name="relay.com", type="relaydomain").exists())


class LimitsTestCase(ModoTestCase, Operations):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(LimitsTestCase, cls).setUpTestData()
        for name, _definition in limits_utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2, app="limits")
        cls.localconfig.save()
        cls.user = UserFactory.create(
            username="reseller", groups=("Resellers",)
        )

    def setUp(self):
        """Initialize test."""
        super(LimitsTestCase, self).setUp()
        self.client.force_login(self.user)

    def test_relay_domains_limit(self):
        self._create_relay_domain(
            "relaydomain1.tld", quota=1, default_mailbox_quota=1)
        self._check_limit("domains", 1, 2)
        self._create_relay_domain(
            "relaydomain2.tld", quota=1, default_mailbox_quota=1)
        self._check_limit("domains", 2, 2)
        self._create_relay_domain("relaydomain3.tld", 403)
        self._check_limit("domains", 2, 2)
        domid = admin_models.Domain.objects.get(name="relaydomain2.tld").id
        self.ajax_post(
            reverse("admin:domain_delete", args=[domid]), {})
        self._check_limit("domains", 1, 2)

    def test_relay_domain_aliases_limit(self):
        self._create_relay_domain(
            "relaydomain1.tld", quota=1, default_mailbox_quota=1)
        domain = admin_models.Domain.objects.get(name="relaydomain1.tld")
        self._relay_domain_alias_operation(
            "add", domain, "relay-domain-alias1.tld"
        )
        self._check_limit("domain_aliases", 1, 2)
        self._relay_domain_alias_operation(
            "add", domain, "relay-domain-alias2.tld"
        )
        self._check_limit("domain_aliases", 2, 2)
        self._relay_domain_alias_operation(
            "add", domain, "relay-domain-alias3.tld", 403
        )
        self._check_limit("domain_aliases", 2, 2)
        self._relay_domain_alias_operation(
            "delete", domain, "relay-domain-alias2.tld"
        )
        self._check_limit("domain_aliases", 1, 2)


class MapFilesTestCase(MapFilesTestCaseMixin, TestCase):

    """Test case for relaydomains."""

    MAP_FILES = [
        "sql-relaydomains.cf",
        "sql-relay-recipient-verification.cf"
    ]


class DataMixin(object):
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        super(DataMixin, cls).setUpTestData()
        transport = tr_factories.TransportFactory(
            pattern="test.com", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": False
            }
        )
        cls.domain1 = admin_factories.DomainFactory(
            name="test.com", type="relaydomain", transport=transport)
        transport = tr_factories.TransportFactory(
            pattern="domain2.test", _settings={
                "relay_target_host": "external.host.tld",
                "relay_target_port": 25,
                "relay_verify_recipients": True
            }
        )
        cls.domain2 = admin_factories.DomainFactory(
            name="test2.com", type="relaydomain", transport=transport)


class RelayDomainAPITestCase(DataMixin, ModoAPITestCase):
    """API test cases."""

    def test_list(self):
        """Test list service."""
        url = reverse("api:relaydomain-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_create(self):
        """Test create service."""
        url = reverse("api:relaydomain-list")
        settings = {
            "relay_target_host": "1.2.3.4"
        }
        data = {
            "name": "test3.com",
            "transport": {
                "service": "relay",
                "_settings": json.dumps(settings)
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["transport"]["_settings"],
            ["relay_target_port: This field is required"]
        )

        settings.update({"relay_target_port": 25})
        data["transport"]["_settings"] = json.dumps(settings)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        domain = admin_models.Domain.objects.get(name="test3.com")
        self.assertEqual(
            domain.transport.next_hop, "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"])
        )

    def test_update(self):
        """Test update service."""
        url = reverse("api:relaydomain-detail", args=[self.domain1.pk])
        settings = self.domain1.transport._settings.copy()
        settings.update({"relay_target_port": 1000})
        data = {
            "name": "test3.com",
            "transport": {
                "service": "relay",
                "_settings": json.dumps(settings)
            }
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.domain1.refresh_from_db()
        self.domain1.transport.refresh_from_db()
        self.assertEqual(self.domain1.name, data["name"])
        self.assertEqual(
            self.domain1.transport.next_hop, "[{}]:{}".format(
                settings["relay_target_host"], settings["relay_target_port"])
        )

    def test_delete(self):
        """Test delete service."""
        url = reverse("api:relaydomain-detail", args=[self.domain1.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(admin_models.Domain.DoesNotExist):
            self.domain1.refresh_from_db()
        self.assertFalse(
            tr_models.Transport.objects.filter(pattern="test.com").exists())
