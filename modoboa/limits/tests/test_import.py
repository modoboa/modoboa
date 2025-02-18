from django.core import exceptions
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
        super().setUpTestData()
        admin_factories.populate_database()
        cls.reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers",)
        )
        cls.dadmin = core_models.User.objects.get(username="admin@test.com")
        cls.domain = admin_models.Domain.objects.get(name="test.com")

    def _test_domain_alias_import(self, limit):
        """Check domain aliases limit."""
        self.client.force_login(self.reseller)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(
            f"""domainalias; domalias1.com; {self.domain}; True
domainalias; domalias2.com; {self.domain}; True
""",
            name="domains.csv",
        )
        self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            f"domainalias; domalias3.com; {self.domain}; True",
            name="domains.csv",
        )
        response = self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
        self.assertContains(response, "Domain aliases: limit reached")

    def _test_domain_admins_import(self, limit, initial_count=0):
        """Check domain admins limit."""
        self.client.force_login(self.reseller)
        self.assertFalse(limit.is_exceeded())
        content = ""
        for cpt in range(initial_count, 2):
            content += (
                f"account; admin{cpt}@{self.domain}; toto; User; One; True; "
                f"DomainAdmins; user{cpt}@{self.domain}; 5; {self.domain}\n"
            )
        f = ContentFile(content, name="domain_admins.csv")
        response = self.client.post(reverse("admin:identity_import"), {"sourcefile": f})
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            f"""account; admin3@{self.domain}; toto; User; One; True; DomainAdmins; admin3@{self.domain}; 5; {self.domain}
""",
            name="domain_admins.csv",
        )  # NOQA:E501
        response = self.client.post(reverse("admin:identity_import"), {"sourcefile": f})
        self.assertContains(response, "Permission denied")

    def _test_mailboxes_import(self, limit):
        """Check mailboxes limit."""
        self.client.force_login(self.dadmin)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(
            f"account; user1@{self.domain}; toto; User; One; True; SimpleUsers; "
            f"user1@{self.domain}; 5\r\n"
            f"account; truc@{self.domain}; toto; René; Truc; True; SimpleUsers; "
            f"truc@{self.domain}; 5\r\n",
            name="domains.csv",
        )
        response = self.client.post(reverse("admin:identity_import"), {"sourcefile": f})
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            f"""
account; user3@{self.domain}; toto; User; One; True; SimpleUsers; user3@{self.domain}; 5
""",
            name="domains.csv",
        )
        response = self.client.post(reverse("admin:identity_import"), {"sourcefile": f})
        self.assertContains(response, "Mailboxes: limit reached")

    def _test_mailbox_aliases_import(self, limit):
        """Check mailbox aliases limit."""
        self.client.force_login(self.dadmin)
        self.assertFalse(limit.is_exceeded())
        f = ContentFile(
            f"""alias; alias1@{self.domain}; True; user@{self.domain}
alias; alias2@{self.domain}; True; user@{self.domain}
""",
            name="aliases.csv",
        )
        self.client.post(reverse("admin:identity_import"), {"sourcefile": f})
        self.assertTrue(limit.is_exceeded())

        f = ContentFile(
            f"""
alias; alias3@{self.domain}; True; user@{self.domain}
""",
            name="aliases.csv",
        )
        with self.assertRaises(exceptions.ValidationError):
            self.client.post(reverse("admin:identity_import"), {"sourcefile": f})


class UserLimitImportTestCase(LimitImportTestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        localconfig = core_models.LocalConfig.objects.first()
        for name, _definition in utils.get_user_limit_templates():
            localconfig.parameters.set_value(f"deflt_user_{name}_limit", 2)
        localconfig.save()
        super().setUpTestData()

    def test_domains_import(self):
        """Check domains limit."""
        self.client.force_login(self.reseller)
        limit = self.reseller.userobjectlimit_set.get(name="domains")
        self.assertFalse(limit.is_exceeded())
        f = ContentFile("domain; domain1.com; 1; 1; True", name="domains.csv")
        self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
        self.assertFalse(limit.is_exceeded())

        f = ContentFile("domain; domain2.com; 0; 1; True", name="domains.csv")
        response = self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
        self.assertContains(response, "not allowed to define unlimited values")

        f = ContentFile("domain; domain2.com; 2; 1; True", name="domains.csv")
        response = self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
        self.assertContains(response, "Quota: limit reached")

        f = ContentFile(
            b"""domain; domain2.com; 1; 1; True
domain; domain3.com; 1000; 100; True
""",
            name="domains.csv",
        )
        response = self.client.post(reverse("admin:domain_import"), {"sourcefile": f})
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
        localconfig.parameters.set_values(
            {"enable_domain_limits": True, "enable_admin_limits": False}
        )
        for name, _definition in utils.get_domain_limit_templates():
            localconfig.parameters.set_value(f"deflt_domain_{name}_limit", 2)
        localconfig.save()
        super().setUpTestData()
        mb = admin_factories.MailboxFactory(
            user__username="user@test4.com", domain__name="test4.com", address="user"
        )
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
