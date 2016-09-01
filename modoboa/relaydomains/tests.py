"""modoboa-admin-relaydomains unit tests."""

from django.core.urlresolvers import reverse
from django.test import TestCase

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core.factories import UserFactory
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase
from modoboa.lib.test_utils import MapFilesTestCaseMixin
from modoboa.limits import utils as limits_utils

from .factories import RelayDomainFactory
from .models import RelayDomain, Service


class Operations(object):

    def _create_relay_domain(self, name, status=200):
        srv, created = Service.objects.get_or_create(name='dummy')
        values = {
            "name": name, "create_dom_admin": "no", "type": "relaydomain",
            "target_host": "external.host.tld", "service": srv.id,
            "enabled": True, "stepid": "step3"
        }
        return self.ajax_post(
            reverse("admin:domain_add"),
            values, status
        )

    def _relay_domain_alias_operation(self, optype, rdomain, name, status=200):
        rdom = RelayDomain.objects.get(domain__name=rdomain)
        values = {
            "name": rdom.domain.name, "target_host": rdom.target_host,
            "type": "relaydomain", "service": rdom.service.id
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
        cls.rdom = RelayDomainFactory(domain__name='relaydomain.tld')
        admin_factories.DomainAliasFactory(
            name='relaydomainalias.tld', target=cls.rdom.domain)
        admin_factories.MailboxFactory(
            domain=cls.rdom.domain, address="local",
            user__username="local@relaydomain.tld",
            user__groups=("SimpleUsers", )
        )

    def test_create_relaydomain(self):
        """Test the creation of a relay domain.

        We also check that unique constraints are respected: domain,
        relay domain alias.

        FIXME: add a check for domain alias.
        """
        self._create_relay_domain('relaydomain1.tld')
        rdom = RelayDomain.objects.get(domain__name='relaydomain1.tld')
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
            'name': "relaydomain.org", "target_host": self.rdom.target_host,
            "type": "relaydomain", "enabled": True,
            "service": self.rdom.service.id
        }
        self.ajax_post(
            reverse('admin:domain_change',
                    args=[self.rdom.domain.id]),
            values
        )
        RelayDomain.objects.get(domain__name='relaydomain.org')

    def test_relaydomain_domain_switch(self):
        """Check domain <-> relaydomain transitions."""
        domain = self.rdom.domain
        values = {
            "name": "relaydomain.tld",
            "type": "domain",
            "enabled": True,
        }
        self.ajax_post(
            reverse('admin:domain_change', args=[domain.pk]), values)
        self.assertFalse(
            RelayDomain.objects.filter(
                domain__name="relaydomain.tld").exists())
        self.assertEqual(
            admin_models.Domain.objects.get(name="relaydomain.tld").type,
            "domain")
        values = {
            "name": "relaydomain.tld",
            "type": "relaydomain",
            "enabled": True,
        }
        self.ajax_post(
            reverse("admin:domain_change", args=[domain.pk]), values)
        self.assertEqual(
            admin_models.Domain.objects.get(name="relaydomain.tld").type,
            "relaydomain")
        self.assertTrue(
            RelayDomain.objects.filter(
                domain__name="relaydomain.tld").exists())

    def test_edit_relaydomainalias(self):
        """Test the modification of a relay domain alias.

        Rename 'relaydomainalias.tld' domain to 'relaydomainalias.net'
        """
        values = {
            "name": "relaydomain.org", "target_host": self.rdom.target_host,
            "type": "relaydomain", "service": self.rdom.service.id,
            "aliases": "relaydomainalias.net"
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
        with self.assertRaises(RelayDomain.DoesNotExist):
            RelayDomain.objects.get(domain__name='relaydomain.tld')

    def test_delete_relaydomainalias(self):
        """Test the removal of a relay domain alias."""
        self._relay_domain_alias_operation(
            'del', self.rdom.domain.name, 'relaydomainalias.tld'
        )
        with self.assertRaises(RelayDomain.DoesNotExist):
            RelayDomain.objects.get(domain__name='relaydomainalias.tld')

    def test_alias_on_relaydomain(self):
        """Create an alias on a relay domain."""
        values = {
            "address": "alias@relaydomain.tld",
            "recipients": "recipient@relaydomain.tld",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        alias = admin_models.Alias.objects.get(address="alias@relaydomain.tld")
        values = {
            "address": "alias2@relaydomain.tld",
            "recipients": "local@relaydomain.tld",
            "enabled": True
        }
        self.ajax_post(reverse("admin:alias_add"), values)
        alias = admin_models.Alias.objects.get(
            address="alias2@relaydomain.tld")


class LimitsTestCase(ModoTestCase, Operations):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(LimitsTestCase, cls).setUpTestData()

        for name, tpl in limits_utils.get_user_limit_templates():
            parameters.save_admin(
                "DEFLT_USER_{0}_LIMIT".format(name.upper()), 2, app="limits"
            )
        cls.user = UserFactory.create(
            username='reseller', groups=('Resellers',)
        )

    def setUp(self):
        """Initialize test."""
        super(LimitsTestCase, self).setUp()
        self.client.logout()
        self.client.login(username='reseller', password='toto')

    def test_relay_domains_limit(self):
        self._create_relay_domain('relaydomain1.tld')
        self._check_limit('domains', 1, 2)
        self._create_relay_domain('relaydomain2.tld')
        self._check_limit('domains', 2, 2)
        self._create_relay_domain('relaydomain3.tld', 403)
        self._check_limit('domains', 2, 2)
        domid = admin_models.Domain.objects.get(name='relaydomain2.tld').id
        self.ajax_post(
            reverse('admin:domain_delete', args=[domid]), {})
        self._check_limit('domains', 1, 2)

    def test_relay_domain_aliases_limit(self):
        self._create_relay_domain('relaydomain1.tld')
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
