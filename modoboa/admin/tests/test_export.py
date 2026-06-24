"""Export related test cases."""

import sys
from io import StringIO

from django.core.management import call_command
from django.urls import reverse
from django.utils.encoding import force_str

from modoboa.lib.csvutils import escape_csv_cell, escape_csv_row
from modoboa.lib.tests import ModoAPITestCase
from .. import factories, models


class CSVInjectionTestCase(ModoAPITestCase):
    """Regression tests for CSV/formula injection (CWE-1236)."""

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_escape_csv_cell(self):
        """Cells starting with a formula trigger are neutralized."""
        for payload in ("=HYPERLINK(1)", "+1", "-1", "@SUM(1)", "\t=1", "\r=1", "\n=1"):
            self.assertEqual(escape_csv_cell(payload), "'" + payload)
        # Harmless values are left untouched.
        for value in ("Léon", "user@test.com", "1+1", ""):
            self.assertEqual(escape_csv_cell(value), value)
        # Non-string values are coerced then checked.
        self.assertEqual(escape_csv_cell(True), "True")

    def test_escape_csv_row(self):
        self.assertEqual(
            escape_csv_row(["account", "=cmd", "ok"]),
            ["account", "'=cmd", "ok"],
        )

    def test_identities_export_neutralizes_formula(self):
        """A user controlled name must not be exported as a live formula."""
        factories.MailboxFactory(
            user__username="evil@test.com",
            user__first_name="=HYPERLINK(0)",
            user__last_name="+SUM(1,1)",
            user__groups=("SimpleUsers",),
            address="evil",
            domain__name="test.com",
        )
        response = self.client.get(reverse("v2:identities-export"))
        content = force_str(response.content)
        self.assertIn("'=HYPERLINK(0)", content)
        self.assertIn("'+SUM(1,1)", content)
        # The raw (unescaped) formula must not appear as a cell value.
        self.assertNotIn(",=HYPERLINK(0),", content)

    def test_domains_export_command_neutralizes_formula(self):
        """The management command export path is escaped too."""
        dom = models.Domain.objects.get(name="test.com")
        factories.DomainAliasFactory(name="=evil.test", target=dom)
        stdout_backup, sys.stdout = sys.stdout, StringIO()
        call_command("modo", "export", "domains")
        response = force_str(sys.stdout.getvalue())
        sys.stdout = stdout_backup
        self.assertIn("domainalias;'=evil.test;test.com;True", response)


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
