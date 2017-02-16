"""Export related test cases."""

from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase

from .. import factories
from .. import models


class ExportTestCase(ModoTestCase):
    """Test case for export operations."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ExportTestCase, cls).setUpTestData()
        factories.populate_database()

    def __export_domains(self, domfilter=""):
        self.client.get(
            "{}?domfilter={}".format(
                reverse("admin:_domain_list"), domfilter))
        return self.client.post(
            reverse("admin:domain_export"), {"filename": "test.csv"}
        )

    def __export_identities(self, idtfilter="", grpfilter=""):
        self.client.get(
            reverse("admin:_identity_list") +
            "?grpfilter=%s&idtfilter=%s" % (grpfilter, idtfilter)
        )
        return self.client.post(
            reverse("admin:identity_export"),
            {"filename": "test.csv"}
        )

    def assertListEqual(self, list1, list2):
        list1 = list1.split("\r\n")
        list2 = list2.split("\r\n")
        self.assertEqual(len(list1), len(list2))
        for entry in list1:
            if not entry:
                continue
            self.assertIn(entry, list2)

    def test_export_domains(self):
        """Check domain export."""
        dom = models.Domain.objects.get(name="test.com")
        factories.DomainAliasFactory(name="alias.test", target=dom)
        response = self.__export_domains()
        expected_response = [
            "domain;test.com;50;10;True",
            "domainalias;alias.test;test.com;True",
            "domain;test2.com;0;0;True",
        ]
        self.assertListEqual(
            "\r\n".join(expected_response),
            response.content.strip()
        )

    def test_export_identities(self):
        response = self.__export_identities()
        self.assertListEqual(
            "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com\r\naccount;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\nalias;alias@test.com;True;user@test.com\r\nalias;forward@test.com;True;user@external.com\r\nalias;postmaster@test.com;True;test@truc.fr;toto@titi.com\r\n",
            response.content.strip()
        )

    def test_export_simpleusers(self):
        response = self.__export_identities(
            idtfilter="account", grpfilter="SimpleUsers"
        )
        self.assertListEqual(
            "account;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10",
            response.content.strip()
        )

    def test_export_superadmins(self):
        """A test to validate we only export 1 super admin.

        The password is removed since it is hashed using SHA512-CRYPT.
        """
        response = self.__export_identities(
            idtfilter="account", grpfilter="SuperAdmins"
        )
        elements = response.content.strip().split(";")
        self.assertEqual(len(elements), 9)
        elements[2] = ""
        self.assertEqual(
            ";".join(elements), "account;admin;;;;True;SuperAdmins;;"
        )

    def test_export_domainadmins(self):
        response = self.__export_identities(
            idtfilter="account", grpfilter="DomainAdmins"
        )
        self.assertListEqual(
            "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com",
            response.content.strip()
        )

    def test_export_aliases(self):
        response = self.__export_identities(idtfilter="alias")
        self.assertEqual(
            response.content.strip(),
            "alias;alias@test.com;True;user@test.com\r\nalias;forward@test.com;True;user@external.com\r\nalias;postmaster@test.com;True;test@truc.fr;toto@titi.com"
        )
