# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import reverse

from modoboa.lib.tests import ModoTestCase
from .. import factories
from ..models import Alias, Domain, DomainAlias


class DomainAliasTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(DomainAliasTestCase, cls).setUpTestData()
        factories.populate_database()
        cls.dom = Domain.objects.get(name="test.com")

    def test_model(self):
        dom = Domain.objects.get(name="test.com")
        domal = DomainAlias()
        domal.name = "domalias.net"
        domal.target = dom
        domal.save()
        self.assertEqual(dom.domainalias_count, 1)
        self.assertTrue(
            Alias.objects.filter(
                address="@{}".format(domal.name)).exists())

        domal.name = "domalias.org"
        domal.save()

        domal.delete()
        self.assertFalse(
            Alias.objects.filter(
                address="@{}".format(domal.name)).exists())

    def test_form(self):
        dom = Domain.objects.get(name="test.com")
        values = {
            "name": dom.name, "quota": dom.quota,
            "default_mailbox_quota": dom.default_mailbox_quota,
            "enabled": dom.enabled, "aliases": "domalias.net",
            "aliases_1": "domaliasé.com", "type": "domain"
        }
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
