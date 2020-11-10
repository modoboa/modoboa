from django.urls import reverse_lazy

from modoboa.lib.tests import ModoTestCase


class OpenAPITestCase(ModoTestCase):
    openapi_schema_url = reverse_lazy('schema')

    def test_unauthorized(self):
        self.client.logout()

        response = self.client.get(self.openapi_schema_url)
        self.assertEqual(response.status_code, 401)

    def test_get_schema(self):
        self.assertEqual(self.openapi_schema_url, "/docs/openapi.json")

        response = self.client.get(self.openapi_schema_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['info'], {
            'title': "Modoboa API",
            'version': "1.0.0",
        })
