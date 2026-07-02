from django.test import TestCase
from django.urls import reverse


class ViewsTestCase(TestCase):

    databases = "__all__"

    def test_autoconfig(self):
        url = reverse("autoconfig:autoconfig")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"%EMAILLOCALPART%@%EMAILDOMAIN%", resp.content)

    def test_autoconfig_empty_emailaddress(self):
        url = reverse("autoconfig:autoconfig")

        resp = self.client.get(f"{url}?emailaddress=")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"%EMAILLOCALPART%@%EMAILDOMAIN%", resp.content)

    def test_autoconfig_with_emailaddress(self):
        url = reverse("autoconfig:autoconfig")

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

    def test_autodiscover_real_outlook_xml_body(self):
        """Real Outlook clients POST an XML body, not form data."""
        url = reverse("autoconfig:autodiscover")
        body = b"""<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006">
  <Request>
    <EMailAddress>test@test.com</EMailAddress>
    <AcceptableResponseSchema>http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a</AcceptableResponseSchema>
  </Request>
</Autodiscover>"""
        resp = self.client.post(url, data=body, content_type="text/xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<LoginName>test@test.com", resp.content)

        resp = self.client.post(url, data=b"not xml", content_type="text/xml")
        self.assertEqual(resp.status_code, 404)

    def test_autodiscover_empty_emailaddress_xml_element(self):
        url = reverse("autoconfig:autodiscover")
        body = b"""<?xml version="1.0" encoding="utf-8"?>
<Autodiscover xmlns="http://schemas.microsoft.com/exchange/autodiscover/outlook/requestschema/2006">
  <Request>
    <EMailAddress></EMailAddress>
    <AcceptableResponseSchema>http://schemas.microsoft.com/exchange/autodiscover/outlook/responseschema/2006a</AcceptableResponseSchema>
  </Request>
</Autodiscover>"""

        resp = self.client.post(url, data=body, content_type="text/xml")
        self.assertEqual(resp.status_code, 404)

    def test_autodiscover_empty_emailaddress_form_field(self):
        url = reverse("autoconfig:autodiscover")

        resp = self.client.post(url, {"EmailAddress": ""})
        self.assertEqual(resp.status_code, 404)

    def test_mobileconfig(self):
        url = reverse("autoconfig:mobileconfig")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get(f"{url}?emailaddress=test@test.com")
        self.assertEqual(resp.status_code, 200)
