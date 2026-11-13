"""OAuth2 validator."""

from oauth2_provider import oauth2_validators


def _is_active(request) -> bool:
    # Tokens issued without a user (client credentials) are not concerned
    return request.user is None or request.user.is_active


class OAuth2Validator(oauth2_validators.OAuth2Validator):
    """Reject tokens of inactive accounts.

    django-oauth-toolkit only checks ``is_active`` for the password grant.
    """

    def validate_bearer_token(self, token, scopes, request):
        return super().validate_bearer_token(token, scopes, request) and _is_active(
            request
        )

    def validate_refresh_token(self, refresh_token, client, request, *args, **kwargs):
        return super().validate_refresh_token(
            refresh_token, client, request, *args, **kwargs
        ) and _is_active(request)
