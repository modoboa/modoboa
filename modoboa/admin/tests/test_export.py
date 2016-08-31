"""Export related test cases."""

from django.core.urlresolvers import reverse

from modoboa.lib.tests import ModoTestCase

from .. import factories


class ExportTestCase(ModoTestCase):

    """Test case for export operations."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(ExportTestCase, cls).setUpTestData()
        factories.populate_database()

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
        list2 = list2.split('\r\n')
        for entry in list1.split('\r\n'):
            if not entry:
                continue
            self.assertIn(entry, list2)

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
