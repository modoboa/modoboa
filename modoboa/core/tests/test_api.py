from django.urls import reverse_lazy

from modoboa.lib.tests import ModoTestCase


class OpenAPITestCase(ModoTestCase):
    openapi_schema_url = reverse_lazy('openapi_schema')

    def test_unauthorized(self):
        self.client.logout()

        response = self.client.get("/docs/api/")
        self.assertRedirects(response, "/accounts/login/?next=/docs/api/")

        response = self.client.get(self.openapi_schema_url)
        self.assertEqual(response.status_code, 403)

    def test_get_schema(self):
        self.assertEqual(self.openapi_schema_url, "/docs/openapi.json")

        response = self.client.get(self.openapi_schema_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['info'], {
            'title': "Modoboa API",
            'version': "1.0.0",
        })

    def test_get_swagger_ui(self):
        response = self.client.get("/docs/api/")
        self.assertContains(response, "Modoboa API")
