from django.test import TestCase
from django.urls import reverse


class ViewsTestCase(TestCase):

    databases = "__all__"

    def test_autoconfig(self):
        url = reverse("autoconfig:autoconfig")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(f"{url}?emailaddress=test@test.com")
        self.assertEqual(resp.status_code, 200)

        self.assertIn(b'<emailProvider id="test.com">', resp.content)

    def test_autodiscover(self):
        url = reverse("autoconfig:autodiscover")

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(url, {"EmailAddress": "test@test.com"})
        self.assertEqual(resp.status_code, 200)

        self.assertIn(b"<LoginName>test@test.com", resp.content)

    def test_mobileconfig(self):
        url = reverse("autoconfig:mobileconfig")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(f"{url}?emailaddress=test@test.com")
        self.assertEqual(resp.status_code, 200)
