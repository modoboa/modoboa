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
