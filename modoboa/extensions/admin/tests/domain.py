from django.core.urlresolvers import reverse
from modoboa.core.models import User
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin.models import (
    Domain, Alias
)
from modoboa.extensions.admin import factories


class DomainTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(DomainTestCase, self).setUp()
        factories.populate_database()

    def test_create(self):
        """Test the creation of a domain
        """
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "no",
            "stepid": 'step2'
        }
        self.ajax_post(reverse("admin:domain_add"), values)
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.name, "pouet.com")
        self.assertEqual(dom.quota, 100)
        self.assertEqual(dom.enabled, False)
        self.assertFalse(dom.admins)

    def test_create_with_template(self):
        """Test the creation of a domain with a template

        """
        values = {
            "name": "pouet.com", "quota": 100, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "stepid": 'step2'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster", domain__name="pouet.com")
        self.assertIn(da.mailbox_set.all()[0], al.mboxes.all())
        self.assertTrue(da.can_access(al))

    def test_create_with_template_and_empty_quota(self):
        """Test the creation of a domain with a template and no quota"""
        values = {
            "name": "pouet.com", "quota": 0, "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "stepid": 'step2'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        da = User.objects.get(username="toto@pouet.com")
        self.assertIn(da, dom.admins)
        al = Alias.objects.get(address="postmaster", domain__name="pouet.com")
        self.assertIn(da.mailbox_set.all()[0], al.mboxes.all())
        self.assertTrue(da.can_access(al))

    def test_create_using_default_quota(self):
        parameters.save_admin('DEFAULT_DOMAIN_QUOTA', 50, app='admin')
        values = {
            "name": "pouet.com", "create_dom_admin": "yes",
            "dom_admin_username": "toto", "create_aliases": "yes",
            "stepid": 'step2'
        }
        self.ajax_post(
            reverse("admin:domain_add"),
            values
        )
        dom = Domain.objects.get(name="pouet.com")
        self.assertEqual(dom.quota, 50)
        da = User.objects.get(username="toto@pouet.com")
        self.assertEqual(da.mailbox_set.all()[0].quota, 50)

    def test_modify(self):
        """Test the modification of a domain

        Rename 'test.com' domain to 'pouet.com'
        """
        values = {
            "name": "pouet.com", "quota": 100, "enabled": True
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
