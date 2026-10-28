"""OAuth 2.0 related utilies."""

import base64


def build_oauthbearer_string(username: str, token: str) -> bytes:
    result = (
        b"n,a="
        + username.encode("utf-8")
        + b",\001auth=Bearer "
        + token.encode("utf-8")
        + b"\001\001"
    )
    return base64.b64encode(result)


def get_access_token(request) -> str | None:
    """Return the raw access token associated to a request.

    django-oauth-toolkit >= 3.4 does not expose the token value through
    ``__str__`` anymore, it must be read from the ``token`` attribute.
    ``request.auth`` can also be ``None`` (session authentication) or a
    simple string, so handle those cases too.

    The value is taken from the ``Authorization`` header first: with
    ``COMPLIANT_BCP_RFC9700_TOKEN_STORAGE`` enabled, the ``token``
    column is left blank and only a checksum is stored.
    """
    auth = getattr(request, "auth", None)
    if auth is None:
        return None
    # Same parsing as oauthlib, so the token is the one that authenticated
    parts = request.META.get("HTTP_AUTHORIZATION", "").split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return getattr(auth, "token", auth)
