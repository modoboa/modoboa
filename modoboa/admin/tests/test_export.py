"""Export related test cases."""

import sys
from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from django.utils.encoding import force_str

from modoboa.lib.tests import ModoAPITestCase
from .. import factories, models


class ExportTestCase(ModoAPITestCase):
    """Test case for export operations."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def __export_domains(self, domfilter=""):
        return self.client.get(reverse("v2:domain-export"))

    def __export_identities(self, idtfilter="", grpfilter=""):
        return self.client.get(reverse("v2:identities-export"))

    def test_export_domains_management_command(self):
        """Check domain export."""
        dom = models.Domain.objects.get(name="test.com")
        factories.DomainAliasFactory(name="alias.test", target=dom)
        expected_response = [
            "domain;test.com;50;10;True",
            "domainalias;alias.test;test.com;True",
            "domain;test2.com;0;0;True",
        ]
        stdout_backup, sys.stdout = sys.stdout, StringIO()
        call_command("modo", "export", "domains")
        response = sys.stdout.getvalue()
        sys.stdout = stdout_backup
        self.assertCountEqual(
            expected_response, force_str(response.strip()).split("\r\n")
        )

    # FIXME: filters are not available yet in the API

    # def test_export_simpleusers(self):
    #     factories.MailboxFactory(
    #         user__username="toto@test.com",
    #         user__first_name="Léon",
    #         user__groups=("SimpleUsers",),
    #         address="toto",
    #         domain__name="test.com",
    #     )
    #     response = self.__export_identities(
    #         idtfilter="account", grpfilter="SimpleUsers"
    #     )
    #     expected_response = "account;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\naccount;toto@test.com;{PLAIN}toto;Léon;;True;SimpleUsers;toto@test.com;10"  # NOQA:E501
    #     self.assertCountEqual(
    #         expected_response.split("\r\n"),
    #         force_str(response.content.strip()).split("\r\n"),
    #     )

    # def test_export_superadmins(self):
    #     """A test to validate we only export 1 super admin.

    #     The password is removed since it is hashed using SHA512-CRYPT.
    #     """
    #     response = self.__export_identities(
    #         idtfilter="account", grpfilter="SuperAdmins"
    #     )
    #     elements = response.content.decode().strip().split(";")
    #     self.assertEqual(len(elements), 9)
    #     elements[2] = ""
    #     self.assertEqual(";".join(elements), "account;admin;;;;True;SuperAdmins;;")

    # def test_export_domainadmins(self):
    #     response = self.__export_identities(
    #         idtfilter="account", grpfilter="DomainAdmins"
    #     )
    #     expected_response = "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com"  # NOQA:E501
    #     self.assertCountEqual(
    #         expected_response.split("\r\n"),
    #         force_str(response.content.strip()).split("\r\n"),
    #     )

    # def test_export_aliases(self):
    #     response = self.__export_identities(idtfilter="alias")
    #     self.assertEqual(
    #         response.content.decode().strip(),
    #         "alias;alias@test.com;True;user@test.com\r\nalias;forward@test.com;True;user@external.com\r\nalias;postmaster@test.com;True;test@truc.fr;toto@titi.com",  # NOQA:E501
    #     )
