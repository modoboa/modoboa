import os
from unittest import mock

import dns.resolver

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from modoboa.core import factories as core_factories
from modoboa.core.models import User
from modoboa.lib.tests import ModoAPITestCase
from . import utils
from .. import factories
from ..models import Alias, Domain


class ImportTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        cls.localconfig.parameters.set_value("enable_admin_limits", False, app="limits")
        cls.localconfig.save()
        factories.populate_database()

    def test_domain_import_bad_syntax(self):
        """Check errors handling."""
        url = reverse("v2:domain-import-from-csv")
        f = ContentFile("domain; domain1.com; 100; True", name="domains.csv")
        response = self.client.post(url, {"sourcefile": f})
        self.assertContains(response, "Invalid line")
        f = ContentFile("domain; domain1.com; XX; 100; True", name="domains.csv")
        response = self.client.post(url, {"sourcefile": f})
        self.assertContains(response, "domain1.com: invalid quota value")
        f = ContentFile("domain; domain1.com; 100; XX; True", name="domains.csv")
        response = self.client.post(url, {"sourcefile": f})
        self.assertContains(response, "domain1.com: invalid default mailbox quota")
        f = ContentFile("domain; domain1.com; 10; 100; True", name="domains.csv")
        response = self.client.post(url, {"sourcefile": f})
        self.assertContains(
            response,
            "domain1.com: default mailbox quota cannot be greater than domain quota",
        )

    @mock.patch.object(dns.resolver.Resolver, "resolve")
    @mock.patch("socket.getaddrinfo")
    def test_domain_import_with_mx_check(self, mock_getaddrinfo, mock_query):
        """Check domain import when MX check is enabled."""
        mock_query.side_effect = utils.mock_dns_query_result
        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        reseller = core_factories.UserFactory(
            username="reseller", groups=("Resellers",)
        )
        self.authenticate_user(reseller)
        self.set_global_parameter("valid_mxs", "192.0.2.1 2001:db8::1")
        self.set_global_parameter("domains_must_have_authorized_mx", True)

        url = reverse("v2:domain-import-from-csv")
        f = ContentFile(b"domain; test3.com; 100; 1; True", name="domains.csv")
        resp = self.client.post(url, {"sourcefile": f})
        self.assertContains(resp, "test3.com: no authorized MX record found for domain")

        mock_getaddrinfo.side_effect = utils.mock_ip_query_result
        f = ContentFile(b"domain; domain1.com; 100; 1; True", name="domains.csv")
        resp = self.client.post(url, {"sourcefile": f})
        self.assertTrue(Domain.objects.filter(name="domain1.com").exists())

    def test_import_domains_with_conflict(self):
        f = ContentFile(
            b"""domain;test.alias;100;10;True
domainalias;test.alias;test.com;True
""",
            name="domains.csv",
        )
        url = reverse("v2:domain-import-from-csv")
        resp = self.client.post(url, {"sourcefile": f})
        self.assertIn("Object already exists: domainalias", resp.content.decode())

    def test_import_for_nonlocal_domain(self):
        """Try to import an account for nonlocal domain."""
        f = ContentFile(
            b"""
account; user1@nonlocal.com; toto; User; One; True; SimpleUsers; user1@nonlocal.com; 0
""",
            name="identities.csv",
        )  # NOQA:E501
        url = reverse("v2:identities-import-from-csv")
        self.client.post(url, {"sourcefile": f, "crypt_password": True})
        self.assertFalse(User.objects.filter(username="user1@nonlocal.com").exists())

    def test_import_invalid_quota(self):
        f = ContentFile(
            b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; ; test.com
""",
            name="identities.csv",
        )  # NOQA:E501
        url = reverse("v2:identities-import-from-csv")
        resp = self.client.post(url, {"sourcefile": f, "crypt_password": True})
        self.assertIn("wrong quota value", resp.content.decode())

    def test_import_domain_by_domainadmin(self):
        """Check if a domain admin is not allowed to import a domain."""
        self.client.logout()
        admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(admin)
        f = ContentFile(
            b"""
domain; domain2.com; 1000; 200; False
""",
            name="identities.csv",
        )
        url = reverse("v2:identities-import-from-csv")
        resp = self.client.post(url, {"sourcefile": f, "crypt_password": True})
        self.assertIn("You are not allowed to import domains", resp.content.decode())
        f = ContentFile(
            b"""
domainalias; domalias1.com; test.com; True
""",
            name="identities.csv",
        )
        resp = self.client.post(url, {"sourcefile": f, "crypt_password": True})
        self.assertIn(
            "You are not allowed to import domain aliases", resp.content.decode()
        )

    def test_import_quota_too_big(self):
        admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(admin)
        f = ContentFile(
            b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 40
""",
            name="identities.csv",
        )
        resp = self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True},
        )
        self.assertIn("test.com: domain quota exceeded", resp.content.decode())

    def test_import_missing_quota(self):
        f = ContentFile(
            b"""
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com
""",
            name="identities.csv",
        )
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True},
        )
        account = User.objects.get(username="user1@test.com")
        self.assertEqual(
            account.mailbox.quota, account.mailbox.domain.default_mailbox_quota
        )

    def test_import_duplicate(self):
        f = ContentFile(
            """
account; admin@test.com; toto; Admin; ; True; DomainAdmins; admin@test.com; 0; test.com
account; truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 0; test.com
""",
            name="identities.csv",
        )  # NOQA:E501
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True, "continue_if_exists": True},
        )
        admin = User.objects.get(username="admin")
        u1 = User.objects.get(username="truc@test.com")
        self.assertTrue(admin.is_owner(u1))

    def test_import_superadmin(self):
        """Check if a domain admin can import a superadmin

        Expected result: no
        """
        admin = User.objects.get(username="admin@test.com")
        self.authenticate_user(admin)
        f = ContentFile(
            b"""
account; sa@test.com; toto; Super; Admin; True; SuperAdmins; superadmin@test.com; 50
""",
            name="identities.csv",
        )  # NOQA:E501
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True, "continue_if_exists": True},
        )
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="sa@test.com")

    def test_import_alias_with_empty_values(self):
        f = ContentFile(
            b"""
alias;user.alias@test.com;True;user@test.com;;;;;;;;;;;;;;;;
""",
            name="identities.csv",
        )
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True, "continue_if_exists": True},
        )
        alias = Alias.objects.get(address="user.alias@test.com")
        self.assertEqual(alias.type, "alias")

    def test_import_account_alias_conflict(self):
        """Specific test for #1144."""
        f = ContentFile(
            b"""
alias;user@test.com;True;admin@test.com
""",
            name="identities.csv",
        )
        self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True},
        )
        self.assertTrue(
            Alias.objects.filter(address="user@test.com", internal=False).exists()
        )

    def test_domains_import_utf8(self):
        f = ContentFile(
            """domain; dómªin1.com; 1000; 100; True
dómain; dómªin2.com; 1000; 100; True
""".encode(),
            name="dómains.csv",
        )
        self.client.post(reverse("v2:domain-import-from-csv"), {"sourcefile": f})
        admin = User.objects.get(username="admin")
        dom = Domain.objects.get(name="dómªin1.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

    def test_import_command_missing_file(self):
        with mock.patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False
            with self.assertRaises(CommandError) as cm:
                call_command("modo", "import", "test.csv")
                ex_message = cm.exception.messages
                self.assertEqual(ex_message, "File not found")

    def test_import_command(self):
        test_file = os.path.join(
            os.path.dirname(__file__), "test_data/import_domains.csv"
        )
        call_command("modo", "import", test_file)

        admin = User.objects.get(username="admin")

        dom = Domain.objects.get(name="domain1.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

        dom = Domain.objects.get(name="dómain2.com")
        self.assertEqual(dom.quota, 2000)
        self.assertEqual(dom.default_mailbox_quota, 200)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

    def test_import_command_non_utf8(self):
        test_file = os.path.join(
            os.path.dirname(__file__), "test_data/import_domains_iso8859.csv"
        )
        call_command("modo", "import", test_file)
        dom = Domain.objects.get(name="dómain2.com")
        self.assertEqual(dom.quota, 2000)

    def test_import_command_duplicates(self):
        test_file = os.path.join(
            os.path.dirname(__file__), "test_data/import_domains_duplicates.csv"
        )
        with self.assertRaises(CommandError) as cm:
            call_command("modo", "import", test_file)
            ex_message = cm.exception.messages
            self.assertTrue(ex_message.startswith("Object already exists: "))

    def test_import_command_duplicates_continue(self):
        test_file = os.path.join(
            os.path.dirname(__file__), "test_data/import_domains_duplicates.csv"
        )
        call_command("modo", "import", "--continue-if-exists", test_file)

        admin = User.objects.get(username="admin")

        dom = Domain.objects.get(name="domain1.com")
        self.assertEqual(dom.quota, 1000)
        self.assertEqual(dom.default_mailbox_quota, 100)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

        dom = Domain.objects.get(name="dómain2.com")
        self.assertEqual(dom.quota, 2000)
        self.assertEqual(dom.default_mailbox_quota, 200)
        self.assertTrue(dom.enabled)
        self.assertTrue(admin.is_owner(dom))

    def test_import_aliases(self):
        f = ContentFile(
            """
account; user1@test.com; toto; User; One; True; SimpleUsers; user1@test.com; 0
account; Truc@test.com; toto; René; Truc; True; DomainAdmins; truc@test.com; 5; test.com
alias; alias1@test.com; True; user1@test.com
""",
            name="identities.csv",
        )  # NOQA:E501
        resp = self.client.post(
            reverse("v2:identities-import-from-csv"),
            {"sourcefile": f, "crypt_password": True},
        )
        self.assertEqual(resp.status_code, 200)

        test_file = os.path.join(
            os.path.dirname(__file__), "test_data/import_aliases.csv"
        )
        with self.assertRaises(CommandError) as cm:
            call_command("modo", "import", test_file)
            ex_message = cm.exception.messages
            self.assertTrue(ex_message.startswith("Object already exists"))

        call_command("modo", "import", "--continue-if-exists", test_file)
