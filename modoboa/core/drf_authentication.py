"""Custom authentication for DRF."""

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_otp.models import Device
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import constants


class NotVerified(APIException):
    status_code = status.HTTP_418_IM_A_TEAPOT
    default_detail = _('Missing 2FA verification.')
    default_code = 'not_verified'


class JWTAuthenticationWith2FA(JWTAuthentication):
    """Add 2FA support."""

    def verify_user(self, request, user):
        header = self.get_header(request)
        raw_token = self.get_raw_token(header)
        validated_token = self.get_validated_token(raw_token)
        url_exceptions = (
            reverse("v2:account-tfa-verify-code"),
        )
        if request.path in url_exceptions:
            return
        if constants.TFA_DEVICE_TOKEN_KEY in validated_token:
            device_id = validated_token[constants.TFA_DEVICE_TOKEN_KEY]
            device = Device.from_persistent_id(device_id)
            if device is not None and device.user_id == user.pk:
                return
        raise NotVerified

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, token = result
        if user.tfa_enabled:
            self.verify_user(request, user)
        return user, token


class SimpleJWTWith2FAScheme(SimpleJWTScheme):
    target_class = 'modoboa.core.drf_authentication.JWTAuthenticationWith2FA'
    name = 'jwt2FAAuth'
