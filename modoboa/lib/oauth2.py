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
    """
    auth = getattr(request, "auth", None)
    if auth is None:
        return None
    return getattr(auth, "token", auth)
