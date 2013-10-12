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
        self.assertEqual(response.content, "account;admin;{CRYPT}dTTsGDkA5ZHKg;;;True;SuperAdmins;\r\naccount;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;test.com\r\naccount;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com\r\n")

    def test_export_simpleusers(self):
        response = self.__export_identities(grpfilter="SimpleUsers")
        self.assertEqual(
            response.content.strip(),
            "account;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com"
        )

    def test_export_superadmins(self):
        response = self.__export_identities(grpfilter="SuperAdmins")
        self.assertEqual(
            response.content.strip(),
            "account;admin;{CRYPT}dTTsGDkA5ZHKg;;;True;SuperAdmins;"
        )

    def test_export_domainadmins(self):
        response = self.__export_identities(grpfilter="DomainAdmins")
        self.assertEqual(
            response.content.strip(),
            "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;test.com"
        )
