"""Calendars permissions."""

from oauth2_provider.models import get_access_token_model
from rest_framework import permissions

#: Name of the OAuth2 application used by Radicale
RADICALE_APPLICATION_NAME = "Radicale"


class IsRadicale(permissions.BasePermission):
    """Allow access to the Radicale server only.

    Radicale authenticates with an access token issued to its OAuth2
    application (client credentials grant).
    """

    def has_permission(self, request, view):
        token = request.auth
        return (
            isinstance(token, get_access_token_model())
            and token.application is not None
            and token.application.name == RADICALE_APPLICATION_NAME
        )
