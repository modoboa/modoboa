"""Authentication of the Radicale server on the API."""

import base64
import binascii
import hashlib

from django.contrib.auth.hashers import check_password, identify_hasher
from django.contrib.auth.models import AnonymousUser
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _

from oauth2_provider.models import get_application_model
from rest_framework import authentication, exceptions, permissions

#: Name of the OAuth2 application used by Radicale
RADICALE_APPLICATION_NAME = "Radicale"

#: Client secrets already verified, to avoid hashing them on each request
#: (application pk -> (stored secret, SHA-256 of the provided secret))
_verified_secrets = {}


def check_client_secret(application, provided_secret):
    """Check the client secret of an OAuth2 application.

    Secrets can be stored hashed or not, as supported by
    django-oauth-toolkit. Hashing a provided secret is slow (PBKDF2), so
    successful checks are remembered for the stored secret.
    """
    stored_secret = application.client_secret
    digest = hashlib.sha256(provided_secret.encode()).hexdigest()
    verified = _verified_secrets.get(application.pk)
    if (
        verified
        and verified[0] == stored_secret
        and constant_time_compare(verified[1], digest)
    ):
        return True
    try:
        identify_hasher(stored_secret)
    except ValueError:
        # Secret is not hashed
        valid = constant_time_compare(provided_secret, stored_secret)
    else:
        valid = check_password(provided_secret, stored_secret)
    if valid:
        _verified_secrets[application.pk] = (stored_secret, digest)
    return valid


class RadicaleAuthentication(authentication.BaseAuthentication):
    """Authenticate the Radicale server with HTTP Basic.

    Credentials are the client id and secret of Radicale's OAuth2
    application.
    """

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if not auth or auth[0].lower() != b"basic":
            return None
        if len(auth) != 2:
            raise exceptions.AuthenticationFailed(_("Invalid basic header."))
        try:
            decoded = base64.b64decode(auth[1], validate=True).decode()
        except (binascii.Error, UnicodeDecodeError):
            raise exceptions.AuthenticationFailed(_("Invalid basic header.")) from None
        client_id, separator, client_secret = decoded.partition(":")
        if not separator:
            raise exceptions.AuthenticationFailed(_("Invalid basic header."))
        application = (
            get_application_model()
            .objects.filter(name=RADICALE_APPLICATION_NAME, client_id=client_id)
            .first()
        )
        if application is None or not check_client_secret(application, client_secret):
            raise exceptions.AuthenticationFailed(_("Invalid client credentials."))
        return (AnonymousUser(), application)

    def authenticate_header(self, request):
        return 'Basic realm="api"'


class IsRadicale(permissions.BasePermission):
    """Allow access to the Radicale server only."""

    def has_permission(self, request, view):
        return isinstance(request.auth, get_application_model())
