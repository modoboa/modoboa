"""API v2 tests."""

from django.urls import reverse

from rest_framework.authtoken.models import Token

from modoboa.admin import factories, models
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase


class DomainViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_create(self):
        url = reverse("v2:domain-list")
        data = {
            "name": "domain.tld",
            "domain_admin": {
                "username": "admin",
                "with_mailbox": True,
                "with_aliases": True
            }
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)

        dom = models.Domain.objects.get(pk=resp.json()["pk"])
        self.assertEqual(len(dom.admins), 1)
        admin = dom.admins.first()
        self.assertTrue(hasattr(admin, "mailbox"))
        self.assertTrue(
            models.Alias.objects.filter(
                address="postmaster@domain.tld").exists()
        )

    def test_delete(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.da_token.key)

        domain = models.Domain.objects.get(name="test2.com")
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)

        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        url = reverse("v2:domain-delete", args=[domain.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)

    def test_administrators(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-administrators", args=[domain.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_administrator(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-add-administrator", args=[domain.pk])
        account = core_models.User.objects.get(username="user@test.com")
        data = {"account": account.pk}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)

    def test_remove_adminstrator(self):
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("v2:domain-remove-administrator", args=[domain.pk])
        account = core_models.User.objects.get(username="user@test.com")
        data = {"account": account.pk}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 200)


class AccountViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_create(self):
        url = reverse("v2:account-list")
        data = {
            "username": "toto@test.com",
            "role": "SimpleUsers",
            "mailbox": {
                "use_domain_quota": True
            },
            "password": "Toto12345",
            "language": "fr",
            "aliases": ["alias3@test.com"]
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            models.Alias.objects.filter(
                address="alias3@test.com").exists()
        )

    def test_create_admin(self):
        url = reverse("v2:account-list")
        data = {
            "username": "superadmin",
            "role": "SuperAdmins",
            "password": "Toto12345",
            "language": "fr",
            "aliases": ["alias3@test.com"]
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_create_with_bad_password(self):
        url = reverse("v2:account-list")
        data = {
            "username": "superadmin",
            "role": "SuperAdmins",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())

        data["password"] = "Toto"
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("password", resp.json())

    def test_validate(self):
        data = {"username": "toto@test.com"}
        url = reverse("v2:account-validate")
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 204)

    def test_random_password(self):
        url = reverse("v2:account-random-password")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("password", resp.json())

    def test_delete(self):
        account = core_models.User.objects.get(username="user@test.com")
        url = reverse("v2:account-delete", args=[account.pk])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 204)
        with self.assertRaises(core_models.User.DoesNotExist):
            account.refresh_from_db()


class IdentityViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_list(self):
        url = reverse("v2:identities-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 8)


class AliasViewSetTestCase(ModoAPITestCase):

    @classmethod
    def setUpTestData(cls):  # NOQA:N802
        """Create test data."""
        super().setUpTestData()
        factories.populate_database()

    def test_validate(self):
        url = reverse("v2:alias-validate")
        data = {"address": "alias@unknown.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        data = {"address": "alias@test.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)

        data = {"address": "alias2@test.com"}
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 204)

    def test_random_address(self):
        url = reverse("v2:alias-random-address")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("address", resp.json())
