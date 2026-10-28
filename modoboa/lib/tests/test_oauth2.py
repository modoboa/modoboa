"""Tests for oauth2."""

from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase

from .. import oauth2


class GetAccessTokenTestCase(SimpleTestCase):
    """Test get_access_token."""

    def _request(self, auth, **headers):
        request = RequestFactory().get("/", headers=headers)
        request.auth = auth
        return request

    def test_no_auth(self):
        request = self._request(None, Authorization="Bearer raw")
        self.assertIsNone(oauth2.get_access_token(request))

    def test_token_redacted_at_rest(self):
        # COMPLIANT_BCP_RFC9700_TOKEN_STORAGE leaves the token column blank
        request = self._request(
            SimpleNamespace(token=""), Authorization="bearer raw-token"
        )
        self.assertEqual(oauth2.get_access_token(request), "raw-token")
        request = self._request(
            SimpleNamespace(token=""), Authorization="Bearer\t  raw-token"
        )
        self.assertEqual(oauth2.get_access_token(request), "raw-token")

    def test_fallback_to_auth(self):
        request = self._request(SimpleNamespace(token="stored"))
        self.assertEqual(oauth2.get_access_token(request), "stored")
        request = self._request("selfservice", Authorization="Basic xxx")
        self.assertEqual(oauth2.get_access_token(request), "selfservice")
