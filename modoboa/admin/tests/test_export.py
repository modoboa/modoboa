"""Export related test cases."""

import sys
from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from django.utils.encoding import force_str

from modoboa.lib.tests import ModoTestCase
from .. import factories, models


class ExportTestCase(ModoTestCase):
    """Test case for export operations."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def __export_domains(self, domfilter=""):
        self.client.get(
            "{}?domfilter={}".format(reverse("admin:_domain_list"), domfilter)
        )
        return self.client.post(
            reverse("admin:domain_export"), {"filename": "test.csv"}
        )

    def __export_identities(self, idtfilter="", grpfilter=""):
        self.client.get(
            reverse("admin:_identity_list")
            + f"?grpfilter={grpfilter}&idtfilter={idtfilter}"
        )
        return self.client.post(
            reverse("admin:identity_export"), {"filename": "test.csv"}
        )

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
        self.assertCountEqual(
            expected_response, force_str(response.content.strip()).split("\r\n")
        )

        # Test management command too.
        stdout_backup, sys.stdout = sys.stdout, StringIO()
        call_command("modo", "export", "domains")
        response = sys.stdout.getvalue()
        sys.stdout = stdout_backup
        self.assertCountEqual(
            expected_response, force_str(response.strip()).split("\r\n")
        )

    def test_export_identities(self):
        response = self.__export_identities()
        expected_response = "account;admin;;;;True;SuperAdmins;;\r\naccount;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com\r\naccount;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\nalias;alias@test.com;True;user@test.com\r\nalias;forward@test.com;True;user@external.com\r\nalias;postmaster@test.com;True;test@truc.fr;toto@titi.com\r\n"  # NOQA:E501
        received_content = force_str(response.content.strip()).split("\r\n")
        # Empty admin password because it is hashed using SHA512-CRYPT
        admin_row = received_content[0].split(";")
        admin_row[2] = ""
        received_content[0] = ";".join(admin_row)
        self.assertCountEqual(expected_response.strip().split("\r\n"), received_content)

    def test_export_simpleusers(self):
        factories.MailboxFactory(
            user__username="toto@test.com",
            user__first_name="Léon",
            user__groups=("SimpleUsers",),
            address="toto",
            domain__name="test.com",
        )
        response = self.__export_identities(
            idtfilter="account", grpfilter="SimpleUsers"
        )
        expected_response = "account;user@test.com;{PLAIN}toto;;;True;SimpleUsers;user@test.com;10\r\naccount;user@test2.com;{PLAIN}toto;;;True;SimpleUsers;user@test2.com;10\r\naccount;toto@test.com;{PLAIN}toto;Léon;;True;SimpleUsers;toto@test.com;10"  # NOQA:E501
        self.assertCountEqual(
            expected_response.split("\r\n"),
            force_str(response.content.strip()).split("\r\n"),
        )

    def test_export_superadmins(self):
        """A test to validate we only export 1 super admin.

        The password is removed since it is hashed using SHA512-CRYPT.
        """
        response = self.__export_identities(
            idtfilter="account", grpfilter="SuperAdmins"
        )
        elements = response.content.decode().strip().split(";")
        self.assertEqual(len(elements), 9)
        elements[2] = ""
        self.assertEqual(";".join(elements), "account;admin;;;;True;SuperAdmins;;")

    def test_export_domainadmins(self):
        response = self.__export_identities(
            idtfilter="account", grpfilter="DomainAdmins"
        )
        expected_response = "account;admin@test.com;{PLAIN}toto;;;True;DomainAdmins;admin@test.com;10;test.com\r\naccount;admin@test2.com;{PLAIN}toto;;;True;DomainAdmins;admin@test2.com;10;test2.com"  # NOQA:E501
        self.assertCountEqual(
            expected_response.split("\r\n"),
            force_str(response.content.strip()).split("\r\n"),
        )

    def test_export_aliases(self):
        response = self.__export_identities(idtfilter="alias")
        self.assertEqual(
            response.content.decode().strip(),
            "alias;alias@test.com;True;user@test.com\r\nalias;forward@test.com;True;user@external.com\r\nalias;postmaster@test.com;True;test@truc.fr;toto@titi.com",  # NOQA:E501
        )
