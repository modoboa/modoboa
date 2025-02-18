"""Core API viewsets."""

from django.utils.translation import gettext as _

import django_otp
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema

from modoboa.lib.throttle import GetThrottleViewsetMixin

from . import serializers


class AccountViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """Account viewset.

    Contains endpoints used to manipulate current user's account.
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = None

    @action(methods=["post"], detail=False, url_path="tfa/setup")
    def tfa_setup(self, request):
        """Initiate TFA setup."""
        instance, created = TOTPDevice.objects.get_or_create(
            user=request.user, defaults={"name": f"{request.user} TOTP device"}
        )
        return response.Response()

    @extend_schema(request=serializers.CheckTFASetupSerializer)
    @action(methods=["post"], detail=False, url_path="tfa/setup/check")
    def tfa_setup_check(self, request):
        """Check TFA setup."""
        serializer = serializers.CheckTFASetupSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        # create static device for recovery purposes
        device = StaticDevice.objects.create(
            user=request.user, name=f"{request.user} static device"
        )
        for _cpt in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
        django_otp.login(self.request, request.user.totpdevice_set.first())
        return response.Response()

    @action(methods=["post"], detail=False, url_path="tfa/disable")
    def tfa_disable(self, request):
        """Disable TFA."""
        serializer = serializers.CheckPasswordTFASerializer(
            data=request.data,
            context={"user": request.user, "remote_addr": request.META["REMOTE_ADDR"]},
        )
        serializer.is_valid(raise_exception=True)
        if not request.user.totp_enabled:
            # We include it as "password" to display the error
            return response.Response({"error": _("2FA is not enabled")}, status=403)
        request.user.totpdevice_set.all().delete()
        request.user.totp_enabled = False
        if not request.user.tfa_enabled:
            request.user.staticdevice_set.all().delete()
        request.user.save()
        return response.Response()

    @extend_schema(tags=["account"])
    @action(methods=["post"], detail=False, url_path="tfa/reset_codes")
    def tfa_reset_codes(self, request, *args, **kwargs):
        """Reset recovery codes."""
        serializer = serializers.CheckPasswordTFASerializer(
            data=request.data,
            context={"user": request.user, "remote_addr": request.META["REMOTE_ADDR"]},
        )
        serializer.is_valid(raise_exception=True)
        device = request.user.staticdevice_set.first()
        if device is None:
            return response.Response({"error": _("2FA is not enabled")}, status=403)
        device.token_set.all().delete()
        for _cpt in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
        return response.Response(
            {"tokens": device.token_set.all().values_list("token", flat=True)}
        )
