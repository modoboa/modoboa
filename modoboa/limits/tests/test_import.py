# coding: utf-8
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse

from modoboa.admin import factories as admin_factories
from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib import parameters
from modoboa.lib.tests import ModoTestCase

from .. import utils


class UserLimitImportTestCase(ModoTestCase):

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(UserLimitImportTestCase, cls).setUpTestData()
        for name, tpl in utils.get_user_limit_templates():
            parameters.save_admin(
                "DEFLT_USER_{}_LIMIT".format(name.upper()), 2)
        admin_factories.populate_database()
        cls.reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers", ))
        cls.dadmin = core_models.User.objects.get(username="admin@test.com")

    def test_domains_import(self):
        """Check domains limit."""
        self.client.login(
            username=self.reseller.username, password="toto")
        limit = self.reseller.userobjectlimit_set.get(name="domains")
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(b"""domain; domain1.com; 100; True
domain; domain2.com; 200; False
""", name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(b"""domain; domain3.com; 100; True
""", name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Domains: limit reached")

    def test_domain_alias_import(self):
        """Check domain aliases limit."""
        self.client.login(
            username=self.reseller.username, password="toto")
        limit = self.reseller.userobjectlimit_set.get(name="domain_aliases")
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(b"""domainalias; domalias1.com; test.com; True
domainalias; domalias2.com; test.com; True
""", name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            "domainalias; domalias3.com; test.com; True", name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Domain aliases: limit reached")

    def test_mailboxes_import(self):
        """Check mailboxes limit."""
        self.client.login(
            username=self.dadmin.username, password="toto")
        limit = self.dadmin.userobjectlimit_set.get(name="mailboxes")
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(b"""account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 5
account; truc@test.com; toto; René; Truc; True; SimpleUsers; truc@test.com; 5
""", name="domains.csv")
        self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile("""
account; user3@test.com; toto; User; One; True; SimpleUsers; user3@test.com; 5
""", name="domains.csv")
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Mailboxes: limit reached")

    # FIXME: aliases, domain admins
