"""IMAP migration tests."""

import os
import shutil
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


# class ViewsTestCase(DataMixin, ModoTestCase):
#     """Views test cases."""

#     def test_index(self):
#         """Test index view."""
#         url = reverse("modoboa_imap_migration:index")
#         response = self.client.get(url)
#         self.assertContains(response, '<div id="app">')


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
        conf = configparser.ConfigParser()
        conf.read(path)
        self.assertTrue(conf.has_section("Account user@test.com"))


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
