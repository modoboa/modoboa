"""API v2 tests."""

from django.urls import reverse

from modoboa.lib.tests import ModoAPITestCase


class TransportViewSetTestCase(ModoAPITestCase):

    def test_list(self):
        url = reverse("v2:transport-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        backends = resp.json()
        self.assertEqual(len(backends), 1)
        self.assertEqual(backends[0]["name"], "relay")
