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
            reverse("modoboa.extensions.admin.views.identity._identities") \
                + "?grpfilter=%s&idtfilter=%s" % (grpfilter, idtfilter)
        )
        return self.clt.post(
            reverse("modoboa.extensions.admin.views.export.export_identities"),
            {"filename": "test.csv"}
        )

    def test_export_identities(self):
        response = self.__export_identities()
        self.assertEqual(response.content, "account;admin;{CRYPT}dTTsGDkA5ZHKg;;;True;SuperAdmins;;\r\naccount;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com\r\naccount;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\nalias;alias@test.com;True;user@test.com\r\nforward;forward@test.com;True;user@external.com\r\ndlist;postmaster@test.com;True;toto@titi.com;test@truc.fr\r\n")

    def test_export_simpleusers(self):
        response = self.__export_identities(
            idtfilter="account", grpfilter="SimpleUsers"
        )
        self.assertEqual(
            response.content.strip(),
            "account;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10"
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
        self.assertEqual(
            response.content.strip(),
            "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com"
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
