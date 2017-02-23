"""modoboa-admin-relaydomains unit tests."""

import json

from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core.factories import UserFactory
from modoboa.lib.tests import ModoTestCase
from modoboa.lib.test_utils import MapFilesTestCaseMixin
from modoboa.limits import utils as limits_utils

from . import models


class Operations(object):

    def _create_relay_domain(self, name, status=200, **kwargs):
        srv, created = models.Service.objects.get_or_create(name='dummy')
        values = {
            "name": name, "create_dom_admin": False, "type": "relaydomain",
            "target_host": "external.host.tld", "target_port": 25,
            "service": srv.id, "enabled": True, "stepid": "step3",
            "quota": 0, "default_mailbox_quota": 0
        }
        values.update(kwargs)
        return self.ajax_post(
            reverse("admin:domain_add"),
            values, status
        )

    def _relay_domain_alias_operation(self, optype, rdomain, name, status=200):
        rdom = models.RelayDomain.objects.get(domain__name=rdomain)
        values = {
            "name": rdom.domain.name, "target_host": rdom.target_host,
            "target_port": rdom.target_port,
            "type": "relaydomain", "service": rdom.service.id,
            "quota": rdom.domain.quota,
            "default_mailbox_quota": rdom.domain.default_mailbox_quota
        }
        aliases = [alias.name for alias in rdom.domain.domainalias_set.all()]
        if optype == 'add':
            aliases.append(name)
        else:
            aliases.remove(name)
        for cpt, alias in enumerate(aliases):
            fname = 'aliases' if not cpt else 'aliases_%d' % cpt
            values[fname] = alias
        return self.ajax_post(
            reverse("admin:domain_change",
                    args=[rdom.domain.id]),
            values, status
        )

    def _check_limit(self, name, curvalue, maxvalue):
        l = self.user.userobjectlimit_set.get(name=name)
        self.assertEqual(l.current_value, curvalue)
        self.assertEqual(l.max_value, maxvalue)


class RelayDomainsTestCase(ModoTestCase, Operations):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(RelayDomainsTestCase, cls).setUpTestData()
        admin_factories.populate_database()
        dom = admin_factories.DomainFactory(
            name="relaydomain.tld", type="relaydomain")
        dom.relaydomain.target_host = "external.host.tld"
        dom.relaydomain.save()
        cls.rdom = dom.relaydomain
        admin_factories.DomainAliasFactory(
            name="relaydomainalias.tld", target=cls.rdom.domain)
        admin_factories.MailboxFactory(
            domain=cls.rdom.domain, address="local",
            user__username="local@relaydomain.tld",
            user__groups=("SimpleUsers", )
        )

    def test_domain_list_view(self):
        """Make sure relaydomain is listed."""
        url = reverse("admin:_domain_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertIn("relaydomain.tld", content["rows"])
        self.assertIn("Relay Domain", content["rows"])

    def test_create_relaydomain(self):
        """Test the creation of a relay domain.

        We also check that unique constraints are respected: domain,
        relay domain alias.

        FIXME: add a check for domain alias.
        """
        self._create_relay_domain('relaydomain1.tld')
        rdom = models.RelayDomain.objects.get(domain__name='relaydomain1.tld')
        self.assertEqual(rdom.target_host, 'external.host.tld')
        self.assertEqual(rdom.service.name, 'dummy')
        self.assertEqual(rdom.domain.enabled, True)
        self.assertEqual(rdom.verify_recipients, False)

        resp = self._create_relay_domain('test.com', 400)
        self.assertEqual(resp['form_errors']['name'][0],
                         'Domain with this Name already exists.')
        resp = self._create_relay_domain('relaydomainalias.tld', 400)
        self.assertEqual(
            resp['form_errors']['name'][0],
            'A domain alias with this name already exists'
        )

    def test_create_relaydomainalias(self):
        """Test the creation of a relay domain alias.

        We also check that unique constraints are respected: domain,
        relay domain.

        FIXME: add a check for domain alias.
        """
        self._relay_domain_alias_operation(
            'add', self.rdom.domain.name, 'relaydomainalias1.tld'
        )
        resp = self._relay_domain_alias_operation(
            'add', self.rdom.domain.name, 'test.com', 400
        )
        self.assertEqual(
            resp['form_errors']['aliases_2'][0],
            'A domain with this name already exists'
        )
        resp = self._relay_domain_alias_operation(
            'add', self.rdom.domain.name, self.rdom.domain.name, 400
        )
        self.assertEqual(
            resp['form_errors']['aliases_2'][0],
            'A domain with this name already exists'
        )

    def test_edit_relaydomain(self):
        """Test the modification of a relay domain.

        Rename 'relaydomain.tld' domain to 'relaydomain.org'
        """
        values = {
            "name": "relaydomain.org", "target_host": self.rdom.target_host,
            "target_port": 4040, "type": "relaydomain", "enabled": True,
            "service": self.rdom.service.id,
            "quota": 0, "default_mailbox_quota": 0
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[self.rdom.domain.id]),
            values
        )
        self.rdom.refresh_from_db()
        self.assertEqual(self.rdom.target_port, 4040)

    def test_relaydomain_domain_switch(self):
        """Check domain <-> relaydomain transitions."""
        domain_pk = self.rdom.domain.pk
        values = {
            "name": "relaydomain.tld",
            "type": "domain",
            "quota": 0,
            "default_mailbox_quota": 0,
            "enabled": True,
            "target_host": self.rdom.target_host,
            "target_port": self.rdom.target_port,
            "service": self.rdom.service.pk
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain_pk]), values)
        self.assertFalse(
            models.RelayDomain.objects.filter(
                domain__pk=domain_pk).exists())
        self.assertEqual(
            admin_models.Domain.objects.get(name="relaydomain.tld").type,
            "domain")
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
        self.assertTrue(
            models.RelayDomain.objects.filter(
                domain__name="relaydomain.tld").exists())

    def test_edit_relaydomainalias(self):
        """Test the modification of a relay domain alias.

        Rename 'relaydomainalias.tld' domain to 'relaydomainalias.net'
        """
        values = {
            "name": "relaydomain.org", "target_host": self.rdom.target_host,
            "target_port": self.rdom.target_port,
            "type": "relaydomain", "service": self.rdom.service.id,
            "aliases": "relaydomainalias.net",
            "quota": 0, "default_mailbox_quota": 0
        }
        self.ajax_post(
            reverse('admin:domain_change',
                    args=[self.rdom.domain.id]),
            values
        )
        admin_models.DomainAlias.objects.get(name='relaydomainalias.net')
        with self.assertRaises(admin_models.DomainAlias.DoesNotExist):
            admin_models.DomainAlias.objects.get(name='relaydomainalias.tld')

    def test_delete_relaydomain(self):
        """Test the removal of a relay domain."""
        self.ajax_post(
            reverse("admin:domain_delete",
                    args=[self.rdom.domain.id]),
            {}
        )
        with self.assertRaises(models.RelayDomain.DoesNotExist):
            models.RelayDomain.objects.get(domain__name='relaydomain.tld')

    def test_delete_relaydomainalias(self):
        """Test the removal of a relay domain alias."""
        self._relay_domain_alias_operation(
            'del', self.rdom.domain.name, 'relaydomainalias.tld'
        )
        with self.assertRaises(models.RelayDomain.DoesNotExist):
            models.RelayDomain.objects.get(domain__name='relaydomainalias.tld')

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
    def setUpTestData(cls):
        """Create test data."""
        super(LimitsTestCase, cls).setUpTestData()
        for name, tpl in limits_utils.get_user_limit_templates():
            cls.localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2, app="limits")
        cls.localconfig.save()
        cls.user = UserFactory.create(
            username='reseller', groups=('Resellers',)
        )

    def setUp(self):
        """Initialize test."""
        super(LimitsTestCase, self).setUp()
        self.client.force_login(self.user)

    def test_relay_domains_limit(self):
        self._create_relay_domain(
            'relaydomain1.tld', quota=1, default_mailbox_quota=1)
        self._check_limit('domains', 1, 2)
        self._create_relay_domain(
            'relaydomain2.tld', quota=1, default_mailbox_quota=1)
        self._check_limit('domains', 2, 2)
        self._create_relay_domain('relaydomain3.tld', 403)
        self._check_limit('domains', 2, 2)
        domid = admin_models.Domain.objects.get(name='relaydomain2.tld').id
        self.ajax_post(
            reverse('admin:domain_delete', args=[domid]), {})
        self._check_limit('domains', 1, 2)

    def test_relay_domain_aliases_limit(self):
        self._create_relay_domain(
            'relaydomain1.tld', quota=1, default_mailbox_quota=1)
        self._relay_domain_alias_operation(
            'add', 'relaydomain1.tld', 'relay-domain-alias1.tld'
        )
        self._check_limit('domain_aliases', 1, 2)
        self._relay_domain_alias_operation(
            'add', 'relaydomain1.tld', 'relay-domain-alias2.tld'
        )
        self._check_limit('domain_aliases', 2, 2)
        self._relay_domain_alias_operation(
            'add', 'relaydomain1.tld', 'relay-domain-alias3.tld', 403
        )
        self._check_limit('domain_aliases', 2, 2)
        self._relay_domain_alias_operation(
            'delete', 'relaydomain1.tld', 'relay-domain-alias2.tld'
        )
        self._check_limit('domain_aliases', 1, 2)


class MapFilesTestCase(MapFilesTestCaseMixin, TestCase):

    """Test case for relaydomains."""

    MAP_FILES = [
        "sql-relaydomains.cf",
        "sql-relaydomains-transport.cf",
        "sql-relay-recipient-verification.cf"
    ]
