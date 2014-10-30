from django.core.urlresolvers import reverse
from modoboa.lib.tests import ModoTestCase
from modoboa.extensions.admin import factories


class ExportTestCase(ModoTestCase):
    fixtures = ["initial_users.json"]

    def setUp(self):
        super(ExportTestCase, self).setUp()
        factories.populate_database()

    def __export_identities(self, idtfilter="", grpfilter=""):
        self.clt.get(
            reverse("admin:_identity_list") \
                + "?grpfilter=%s&idtfilter=%s" % (grpfilter, idtfilter)
        )
        return self.clt.post(
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
            "account;admin;{CRYPT}dTTsGDkA5ZHKg;;;True;SuperAdmins;;\r\naccount;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com\r\naccount;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\nalias;alias@test.com;True;user@test.com\r\nforward;forward@test.com;True;user@external.com\r\ndlist;postmaster@test.com;True;toto@titi.com;test@truc.fr\r\n",
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
        response = self.__export_identities(
            idtfilter="account", grpfilter="SuperAdmins"
        )
        self.assertEqual(
            response.content.strip(),
            "account;admin;{CRYPT}dTTsGDkA5ZHKg;;;True;SuperAdmins;;"
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
            "alias;alias@test.com;True;user@test.com"
        )

    def test_export_forwards(self):
        response = self.__export_identities(idtfilter="forward")
        self.assertEqual(
            response.content.strip(),
            "forward;forward@test.com;True;user@external.com"
        )

    def test_export_dlists(self):
        response = self.__export_identities(idtfilter="dlist")
        self.assertEqual(
            response.content.strip(),
            "dlist;postmaster@test.com;True;toto@titi.com;test@truc.fr"
        )
