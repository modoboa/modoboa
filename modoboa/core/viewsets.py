"""Core API viewsets."""

from django.utils.translation import ugettext as _

import django_otp
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from . import serializers


class AccountViewSet(viewsets.ViewSet):
    """Account viewset.

    Contains endpoints used to manipulate current user's account.
    """

    permission_classes = (permissions.IsAuthenticated, )

    @action(methods=["post"], detail=False, url_path="tfa/setup")
    def tfa_setup(self, request):
        """Initiate TFA setup."""
        instance, created = TOTPDevice.objects.get_or_create(
            user=request.user,
            defaults={"name": "{} TOTP device".format(request.user)}
        )
        return response.Response()

    @action(methods=["post"], detail=False, url_path="tfa/setup/check")
    def tfa_setup_check(self, request):
        """Check TFA setup."""
        serializer = serializers.CheckTFASetupSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        # create static device for recovery purposes
        device = StaticDevice.objects.create(
            user=request.user,
            name="{} static device".format(request.user)
        )
        for cpt in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
        django_otp.login(self.request, request.user.totpdevice_set.first())
        return response.Response()

    @action(methods=["post"], detail=False, url_path="tfa/disable")
    def tfa_disable(self, request):
        """Disable TFA."""
        if not request.user.tfa_enabled:
            return response.Response({"error": _("2FA is not enabled")},
                                     status=400)
        request.user.totpdevice_set.all().delete()
        request.user.staticdevice_set.all().delete()
        request.user.tfa_enabled = False
        request.user.save()
        return response.Response()

    @action(methods=["post"], detail=False, url_path="tfa/reset_codes")
    def tfa_reset_codes(self, request, *args, **kwargs):
        """Reset recovery codes."""
        device = request.user.staticdevice_set.first()
        if device is None:
            return response.Response(status=403)
        device.token_set.all().delete()
        for cpt in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
        return response.Response({
            "tokens": device.token_set.all().values_list("token", flat=True)
        })
