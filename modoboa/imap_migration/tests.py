"""IMAP migration tests."""

import os
import shutil
import stat
import tempfile
from unittest import mock

from six.moves import configparser

from django.core.management import call_command
from django.urls import reverse

from modoboa.admin import factories as admin_factories
from modoboa.admin import models as admin_models
from modoboa.core import factories as core_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase, ModoAPITestCase

from . import checks
from . import factories
from . import models


class DataMixin:
    """A mixin to provide test data."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        admin_factories.populate_database()
        cls.mb = admin_models.Mailbox.objects.get(user__username="user@test.com")
        cls.migration = factories.MigrationFactory(
            password="Toto1234", mailbox=cls.mb, username="user@test.com"
        )


class AuthenticationTestCase(DataMixin, ModoTestCase):
    """IMAP authentication test case."""

    @mock.patch("imaplib.IMAP4")
    def test_authentication(self, mock_imap):
        """Check IMAP authentication."""
        factories.EmailProviderDomainFactory(name="test.com")
        mock_imap.return_value.login.return_value = ["OK", b""]
        url = reverse("core:login")
        data = {"username": "new_user@test.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        user = core_models.User.objects.get(username="new_user@test.com")
        self.assertEqual(user.mailbox.domain.name, "test.com")

        mock_imap.return_value.login.return_value = ["NO", b"Error"]
        data = {"username": "new_user@test.com", "password": "Toto123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

        mock_imap.return_value.login.return_value = ["OK", b""]
        data = {"username": "new_user@test2.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

        self.set_global_parameter("auto_create_domain_and_mailbox", False, app="admin")
        data = {"username": "new_user2@test.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

    @mock.patch("imaplib.IMAP4")
    def test_authentication_forbidden_characters(self, mock_imap):
        """Credentials with control characters must be rejected.

        Both values end up in the generated offlineimap configuration
        file: a newline would allow injecting arbitrary directives.
        """
        factories.EmailProviderDomainFactory(name="test.com")
        mock_imap.return_value.login.return_value = ["OK", b""]
        url = reverse("core:login")
        data = {"username": "new_user@test.com", "password": "Toto1234\nssl = no"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            core_models.User.objects.filter(username="new_user@test.com").exists()
        )

    @mock.patch("imaplib.IMAP4")
    def test_authenticate_and_rename(self, mock_imap):
        """Check address renaming."""
        domain = admin_models.Domain.objects.get(name="test.com")
        factories.EmailProviderDomainFactory(name="gmail.com", new_domain=domain)
        mock_imap.return_value.login.return_value = ["OK", b""]
        url = reverse("core:login")
        data = {"username": "new_user@gmail.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        user = core_models.User.objects.get(username="new_user@test.com")
        self.assertEqual(user.mailbox.domain.name, "test.com")

    @mock.patch("imaplib.IMAP4")
    def test_authenticate_conflicts(self, mock_imap):
        """Check potential conflicts."""
        core_factories.UserFactory(
            username="admin2@test.com", groups=("DomainAdmins",), password="{PLAIN}toto"
        )
        domain = admin_models.Domain.objects.get(name="test.com")
        factories.EmailProviderDomainFactory(name="gmail.com", new_domain=domain)
        mock_imap.return_value.login.return_value = ["OK", b""]
        url = reverse("core:login")
        data = {"username": "admin@gmail.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)

        data = {"username": "admin2@gmail.com", "password": "Toto1234"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 401)


class ManagementCommandTestCase(DataMixin, ModoTestCase):
    """Management command test cases."""

    def setUp(self):
        super().setUp()
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def test_generate_offlineimap_config(self):
        """Test generate_offlineimap_config command."""
        path = os.path.join(self.workdir, "offlineimap.conf")
        call_command("generate_offlineimap_config", "--output", path)
        self.assertTrue(os.path.exists(path))
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), stat.S_IRUSR | stat.S_IWUSR)
        conf = configparser.ConfigParser()
        conf.read(path)
        self.assertTrue(conf.has_section("Account user@test.com"))


    def test_generate_offlineimap_config_norestrict(self):
        """Test generate_offlineimap_config command with --no-restrict."""
        # Read umask (never do this in multi-threaded code!)
        umask = os.umask(0)  # Reads current umask, replacing it with 0
        os.umask(umask)  # Restores umask

        # Test that generated file has default umask restrictions
        path = os.path.join(self.workdir, "offlineimap.conf")
        call_command("generate_offlineimap_config", "--output", path, "--no-restrict")
        self.assertTrue(os.path.exists(path))
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), (0o666 & ~umask))

    def test_password_escaping(self):
        """Check that passwords are escaped when needed."""
        self.migration.password = "%Test1234"
        self.migration.save()
        path = os.path.join(self.workdir, "offlineimap.conf")
        call_command("generate_offlineimap_config", "--output", path)
        self.assertTrue(os.path.exists(path))
        conf = configparser.ConfigParser()
        conf.read(path)
        section = "Repository Local_user@test.com"
        self.assertEqual(conf.get(section, "remotepass"), "%Test1234")

        self.migration.password = "Test&1234"
        self.migration.save()
        call_command("generate_offlineimap_config", "--output", path)
        self.assertTrue(os.path.exists(path))
        conf = configparser.ConfigParser()
        conf.read(path)
        section = "Repository Local_user@test.com"
        self.assertEqual(conf.get(section, "remotepass"), self.migration.password)


class ViewSetTestCase(DataMixin, ModoAPITestCase):
    """ViewSet related tests."""

    def test_create_provider(self):
        url = reverse("v2:emailprovider-list")
        data = {
            "name": "Google",
            "address": "imap.google.com",
            "port": 143,
            "secured": True,
            "domains": [{"id": 1000, "name": "gmail.com"}],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            models.EmailProviderDomain.objects.filter(name="gmail.com").exists()
        )

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Migrated domain with name gmail.com already exists",
        )

    def test_migration_list_cross_tenant_isolation(self):
        """A user must not see migrations/providers of other tenants.

        Reproduces MODOBOA-F02: an authenticated SimpleUser of test2.com
        used to be able to list migrations and providers belonging to
        test.com through GET /api/v2/migrations/ and
        /api/v2/email-providers/.
        """
        # cls.migration targets user@test.com (see DataMixin).
        factories.EmailProviderDomainFactory(
            provider=self.migration.provider,
            name="legacy-test.com",
            new_domain=admin_models.Domain.objects.get(name="test.com"),
        )
        migration_url = reverse("v2:migration-list")
        provider_url = reverse("v2:emailprovider-list")

        # SuperAdmin sees everything.
        for url in (migration_url, provider_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 1)

        # SimpleUser of test2.com sees nothing belonging to test.com.
        attacker = core_models.User.objects.get(username="user@test2.com")
        self.authenticate_user(attacker)
        for url in (migration_url, provider_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

        # DomainAdmin of test2.com must not see test.com data either.
        admin2 = core_models.User.objects.get(username="admin@test2.com")
        self.authenticate_user(admin2)
        for url in (migration_url, provider_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])

        # The legitimate SimpleUser (owner of the mailbox) sees its migration.
        owner = core_models.User.objects.get(username="user@test.com")
        self.authenticate_user(owner)
        response = self.client.get(migration_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # DomainAdmin of test.com sees its tenant's data.
        admin1 = core_models.User.objects.get(username="admin@test.com")
        self.authenticate_user(admin1)
        for url in (migration_url, provider_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()), 1)

    def test_check_connection_denied_to_simple_users(self):
        """check_connection/check_associated_domain are setup-only actions.

        A SimpleUser must not be able to trigger outbound IMAP connections
        or probe domains through these endpoints.
        """
        check_url = reverse("v2:emailprovider-check-connection")
        domain_url = reverse("v2:emailprovider-check-associated-domain")

        attacker = core_models.User.objects.get(username="user@test2.com")
        self.authenticate_user(attacker)
        with mock.patch("imaplib.IMAP4_SSL") as mock_imap:
            response = self.client.post(
                check_url,
                {"address": "imap.example.test", "port": 993, "secured": True},
                format="json",
            )
        self.assertEqual(response.status_code, 403)
        mock_imap.assert_not_called()

        response = self.client.post(
            domain_url, {"name": "legacy-test.com"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

        # A privileged user is still allowed.
        admin1 = core_models.User.objects.get(username="admin@test.com")
        self.authenticate_user(admin1)
        with mock.patch("imaplib.IMAP4_SSL"):
            response = self.client.post(
                check_url,
                {"address": "imap.example.test", "port": 993, "secured": True},
                format="json",
            )
        self.assertEqual(response.status_code, 200)

    def test_update_provider(self):
        provider_domain = factories.EmailProviderDomainFactory(name="outlook.com")
        url = reverse("v2:emailprovider-detail", args=[provider_domain.provider.pk])
        data = {
            "id": provider_domain.provider.id,
            "name": provider_domain.provider.name,
            "address": provider_domain.provider.address,
            "port": provider_domain.provider.port,
            "domains": [
                {"id": provider_domain.id, "name": "hotmail.com", "new_domain": None},
                {
                    "name": "gmail.com",
                    "new_domain": admin_models.Domain.objects.get(name="test.com").pk,
                },
            ],
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        provider_domain.refresh_from_db()
        self.assertEqual(provider_domain.name, data["domains"][0]["name"])
        self.assertTrue(
            models.EmailProviderDomain.objects.filter(name="gmail.com").exists()
        )
        data["domains"].pop()
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            models.EmailProviderDomain.objects.filter(name="gmail.com").exists()
        )


class ChecksTestCase(ModoTestCase):
    """Deploy checks test case."""

    def test_auto_creation_check(self):
        self.assertEqual(checks.check_auto_creation_is_enabled(None), [])
        self.set_global_parameter("auto_create_domain_and_mailbox", False, app="admin")
        self.assertEqual(checks.check_auto_creation_is_enabled(None), [checks.W001])


class SettingsTestCase(ModoAPITestCase):
    """Global parameters validation test case."""

    def _update(self, data):
        url = reverse("v2:parameter-global-detail", args=["imap_migration"])
        return self.client.put(url, data, format="json")

    def test_folder_filters_reject_code_injection(self):
        """Folder filters must not allow breaking out of the offlineimap config.

        ``folder_filter_exclude`` and ``folder_filter_include`` are
        interpolated into Python expressions evaluated by offlineimap. A
        single quote would let a SuperAdmin escape the surrounding string
        literal and achieve arbitrary code execution (CWE-94).
        """
        # PoC payload from the report.
        payload = (
            ".*)', folder) or __import__('os').system('id > /tmp/pwned') "
            "or re.search('(.*"
        )
        response = self._update({"folder_filter_exclude": payload})
        self.assertEqual(response.status_code, 400)
        self.assertIn("folder_filter_exclude", response.json())

        response = self._update({"folder_filter_include": "a','b']);__import__"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("folder_filter_include", response.json())

        # A newline could inject extra offlineimap config directives.
        response = self._update({"folder_filter_exclude": "Trash\npythonfile = /x"})
        self.assertEqual(response.status_code, 400)

    def test_folder_filter_exclude_rejects_invalid_regex(self):
        response = self._update({"folder_filter_exclude": "(unbalanced"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("folder_filter_exclude", response.json())

    def test_legitimate_folder_filters_accepted(self):
        response = self._update(
            {
                "folder_filter_exclude": "^Trash$|Del",
                "folder_filter_include": "debian.user, debian.personal",
            }
        )
        self.assertEqual(response.status_code, 200)
