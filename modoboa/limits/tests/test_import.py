from django.core.files.base import ContentFile
from django.urls import reverse

from modoboa.admin import factories as admin_factories, models as admin_models
from modoboa.core import factories as core_factories, models as core_models
from modoboa.lib.tests import ModoTestCase
from .. import utils


class LimitImportTestCase(ModoTestCase):
    """Base class to test limits."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super(LimitImportTestCase, cls).setUpTestData()
        admin_factories.populate_database()
        cls.reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers", ))
        cls.dadmin = core_models.User.objects.get(username="admin@test.com")
        cls.domain = admin_models.Domain.objects.get(name="test.com")

    def _test_domain_alias_import(self, limit):
        """Check domain aliases limit."""
        self.client.force_login(self.reseller)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile("""domainalias; domalias1.com; {domain}; True
domainalias; domalias2.com; {domain}; True
""".format(domain=self.domain), name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            "domainalias; domalias3.com; {}; True".format(self.domain),
            name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Domain aliases: limit reached")

    def _test_domain_admins_import(self, limit, initial_count=0):
        """Check domain admins limit."""
        self.client.force_login(self.reseller)
        self.assertFalse(limit.is_exceeded())
        content = ""
        for cpt in range(initial_count, 2):
            content += (
                "account; admin{cpt}@{domain}; toto; User; One; True; "
                "DomainAdmins; user{cpt}@{domain}; 5; {domain}\n"
                .format(domain=self.domain, cpt=cpt)
            )
        f = ContentFile(content, name="domain_admins.csv")
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile("""account; admin3@{domain}; toto; User; One; True; DomainAdmins; admin3@{domain}; 5; {domain}
""".format(domain=self.domain), name="domain_admins.csv")  # NOQA:E501
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Permission denied")

    def _test_mailboxes_import(self, limit):
        """Check mailboxes limit."""
        self.client.force_login(self.dadmin)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(
            "account; user1@{domain}; toto; User; One; True; SimpleUsers; "
            "user1@{domain}; 5\r\n"
            "account; truc@{domain}; toto; René; Truc; True; SimpleUsers; "
            "truc@{domain}; 5\r\n".format(domain=self.domain),
            name="domains.csv"
        )
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile("""
account; user3@{domain}; toto; User; One; True; SimpleUsers; user3@{domain}; 5
""".format(domain=self.domain), name="domains.csv")
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Mailboxes: limit reached")

    def _test_mailbox_aliases_import(self, limit):
        """Check mailbox aliases limit."""
        self.client.force_login(self.dadmin)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile("""alias; alias1@{domain}; True; user@{domain}
alias; alias2@{domain}; True; user@{domain}
""".format(domain=self.domain), name="aliases.csv")
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertTrue(limit.is_exceeded())

        f = ContentFile("""
alias; alias3@{domain}; True; user@{domain}
""".format(domain=self.domain), name="aliases.csv")
        response = self.client.post(
            reverse("admin:identity_import"), {
                "sourcefile": f
            }
        )
        self.assertContains(response, "Mailbox aliases: limit reached")


class UserLimitImportTestCase(LimitImportTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        localconfig = core_models.LocalConfig.objects.first()
        for name, _definition in utils.get_user_limit_templates():
            localconfig.parameters.set_value(
                "deflt_user_{0}_limit".format(name), 2)
        localconfig.save()
        super(UserLimitImportTestCase, cls).setUpTestData()

    def test_domains_import(self):
        """Check domains limit."""
        self.client.force_login(self.reseller)
        limit = self.reseller.userobjectlimit_set.get(name="domains")
        self.assertFalse(limit.is_exceeded())
        f = ContentFile("domain; domain1.com; 1; 1; True", name="domains.csv")
        self.client.post(
            reverse("admin:domain_import"), {"sourcefile": f}
        )
        self.assertFalse(limit.is_exceeded())

        f = ContentFile("domain; domain2.com; 0; 1; True", name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {"sourcefile": f}
        )
        self.assertContains(
            response, "not allowed to define unlimited values")

        f = ContentFile("domain; domain2.com; 2; 1; True", name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {"sourcefile": f}
        )
        self.assertContains(response, "Quota: limit reached")

        f = ContentFile(b"""domain; domain2.com; 1; 1; True
domain; domain3.com; 1000; 100; True
""", name="domains.csv")
        response = self.client.post(
            reverse("admin:domain_import"), {"sourcefile": f}
        )
        self.assertContains(response, "Domains: limit reached")

    def test_domain_alias_import(self):
        """Check domain aliases limit."""
        limit = self.reseller.userobjectlimit_set.get(name="domain_aliases")
        self._test_domain_alias_import(limit)

    def test_domain_admins_import(self):
        """Check domain admins limit."""
        self.domain.add_admin(self.reseller)
        limit = self.reseller.userobjectlimit_set.get(name="domain_admins")
        self._test_domain_admins_import(limit)

    def test_mailboxes_import(self):
        """Check mailboxes limit."""
        limit = self.dadmin.userobjectlimit_set.get(name="mailboxes")
        self._test_mailboxes_import(limit)

    def test_mailbox_aliases_import(self):
        """Check mailbox aliases limit."""
        limit = self.dadmin.userobjectlimit_set.get(name="mailbox_aliases")
        self._test_mailbox_aliases_import(limit)


class DomainLimitImportTestCase(LimitImportTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        localconfig = core_models.LocalConfig.objects.first()
        localconfig.parameters.set_values({
            "enable_domain_limits": True,
            "enable_admin_limits": False
        })
        for name, _definition in utils.get_domain_limit_templates():
            localconfig.parameters.set_value(
                "deflt_domain_{0}_limit".format(name), 2)
        localconfig.save()
        super(DomainLimitImportTestCase, cls).setUpTestData()
        mb = admin_factories.MailboxFactory(
            user__username="user@test4.com",
            domain__name="test4.com", address="user")
        cls.domain = mb.domain

    def test_domain_alias_import(self):
        """Check domain aliases limit."""
        limit = self.domain.domainobjectlimit_set.get(name="domain_aliases")
        self._test_domain_alias_import(limit)

    def test_mailboxes_import(self):
        """Check mailboxes limit."""
        self.domain.add_admin(self.dadmin)
        limit = self.domain.domainobjectlimit_set.get(name="mailboxes")
        self._test_mailboxes_import(limit)

    def test_mailbox_aliases_import(self):
        """Check mailbox aliases limit."""
        self.domain.add_admin(self.dadmin)
        limit = self.domain.domainobjectlimit_set.get(name="mailbox_aliases")
        self._test_mailbox_aliases_import(limit)
