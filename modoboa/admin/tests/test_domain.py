# coding: utf-8

"""Domain related test cases."""

import json

from django.core.urlresolvers import reverse

from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase

from .. import factories
from ..models import Domain, Alias


class DomainTestCase(ModoTestCase):

    """Test case for Domain."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(DomainTestCase, cls).setUpTestData()
        factories.populate_database()

    def test_create(self):
        """Test the creation of a domain."""
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "no",
            "type": "domain", "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_utf8(self):
        """Test the creation of a domain with non-ASCII characters."""
        values = {
            "name": "pouét.com", "quota": 100, "create_dom_admin": "no",
            "type": "domain", "stepid": "step3"
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name=u"pouét.com")
        self.assertEqual(dom.name, u"pouét.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_with_template(self):
        """Test the creation of a domain with a template

        """
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "type": "domain", "stepid": 'step3'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(
            al.aliasrecipient_set.filter(r_mailbox=da.mailbox)
            .exists()
        )
        self.assertTrue(da.can_access(al))

    def test_create_with_template_and_empty_quota(self):
        """Test the creation of a domain with a template and no quota"""
        values = {
            "name": "pouet.com", "quota": 0, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "type": "domain", "stepid": 'step3'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster@pouet.com")
        self.assertTrue(
            al.aliasrecipient_set.filter(r_mailbox=da.mailbox)
            .exists()
        )
        self.assertTrue(da.can_access(al))

    def test_create_using_default_quota(self):
        parameters.save_admin('DEFAULT_DOMAIN_QUOTA', 50, app='admin')
        values = {
            "name": "pouet.com", "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "type": "domain", "stepid": 'step3'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.quota, 50)
        da = User.objects.get(username="toto@pouet.com")
        self.assertEqual(da.mailbox.quota, 50)

    def test_modify(self):
        """Test the modification of a domain

        Rename 'test.com' domain to 'pouet.com'
        """
        values = {
            "name": "pouet.com", "quota": 100, "type": "domain",
            "enabled": True
        }
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(
            reverse("admin:domain_change", args=[dom.id]),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertTrue(dom.enabled)

    def test_delete(self):
        """Test the removal of a domain
        """
        dom = Domain.objects.get(name="test.com")
        self.ajax_post(
            reverse("admin:domain_delete", args=[dom.id]),
            {}
        )
        with self.assertRaises(Domain.DoesNotExist):
            Domain.objects.get(pk=1)

    def test_domain_flat_list(self):
        """Test the 'domain_flat_list' view."""
        response = self.client.get(reverse("admin:domain_flat_list"))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertIn("test.com", content)
        self.assertIn("test2.com", content)
