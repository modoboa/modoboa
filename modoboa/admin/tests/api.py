"""Admin API related tests."""

from django.core.urlresolvers import reverse

from rest_framework.authtoken.models import Token

from modoboa.core import models as core_models
from modoboa.lib.tests import ModoAPITestCase

from .. import factories
from .. import models


class APITestCase(ModoAPITestCase):

    """Check API."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super(APITestCase, cls).setUpTestData()
        factories.populate_database()
        cls.da_token = Token.objects.create(
            user=core_models.User.objects.get(username="admin@test.com"))

    def test_get_domains(self):
        """Retrieve a list of domains."""
        url = reverse("external_api:domain-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        url = reverse(
            "external_api:domain-detail", args=[response.data[0]["pk"]])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "test2.com")

    def test_create_domain(self):
        """Check domain creation."""
        url = reverse("external_api:domain-list")
        response = self.client.post(url, {"name": "test3.com", "quota": 10})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            models.Domain.objects.filter(name="test3.com").exists())
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data)
        self.assertIn("quota", response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.da_token.key)
        response = self.client.post(url, {"name": "test4.com", "quota": 10})
        self.assertEqual(response.status_code, 403)

    def test_update_domain(self):
        """Check domain update."""
        domain = models.Domain.objects.get(name="test.com")
        url = reverse("external_api:domain-detail", args=[domain.pk])
        response = self.client.put(url, {"name": "test.com", "quota": 1000})
        self.assertEqual(response.status_code, 200)
        domain.refresh_from_db()
        self.assertEqual(domain.quota, 1000)

        response = self.client.put(url, {"name": "test42.com", "quota": 1000})
        self.assertEqual(response.status_code, 200)
        
