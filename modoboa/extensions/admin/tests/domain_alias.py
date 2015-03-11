from django.core.urlresolvers import reverse
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin.models import (
    Domain, DomainAlias
)
from modoboa.extensions.admin import factories


class DomainAliasTestCase(ModoTestCase):
    fixtures = ['initial_users.json']

    def setUp(self):
        super(DomainAliasTestCase, self).setUp()
        factories.populate_database()
        self.dom = Domain.objects.get(name='test.com')

    def test_model(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.enabled = True
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)

        domal.name = "domalias.org"
        domal.save()

        domal.delete()

    def test_form(self):
        dom = Domain.objects.get(name="test.com")
        values = dict(name=dom.name, quota=dom.quota, enabled=dom.enabled,
                      aliases="domalias.net", aliases_1="domalias.com")
        self.ajax_post(
            reverse("admin:domain_change",
                    args=[dom.id]),
            values
        )
        self.assertEqual(dom.domainalias_set.count(), 2)

        del values["aliases_1"]
        self.ajax_post(
            reverse("admin:domain_change",
                    args=[dom.id]),
            values
        )
        self.assertEqual(dom.domainalias_set.count(), 1)
