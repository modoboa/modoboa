"""Core API v2 viewsets."""

import io

import qrcode
import qrcode.image.svg

from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.core.api.v1 import serializers as core_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets
from modoboa.lib import pagination

from ... import constants
from ... import models
from . import serializers


class AccountViewSet(core_v1_viewsets.AccountViewSet):
    """Account viewset."""

    @action(methods=["get"], detail=False)
    @extend_schema(responses=admin_v1_serializers.AccountSerializer)
    def me(self, request):
        """Return information about connected user."""
        serializer = admin_v1_serializers.AccountSerializer(request.user)
        return response.Response(serializer.data)

    @action(
        methods=['post'],
        detail=False,
        url_path='me/password',
        serializer_class=serializers.CheckPasswordSerializer
    )
    def check_me_password(self, request):
        """Check current user password."""
        serializer = serializers.CheckPasswordSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        return response.Response()

    @action(methods=["post"], detail=False, url_path="tfa/verify")
    def tfa_verify_code(self, request):
        """Verify given code validity."""
        serializer = serializers.VerifyTFACodeSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(request.user)
        refresh[constants.TFA_DEVICE_TOKEN_KEY] = (
            serializer.validated_data["code"].persistent_id)
        return response.Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

    @action(methods=["get"], detail=False, url_path="tfa/setup/qr_code")
    def tfa_setup_get_qr_code(self, request):
        """Get a QR code to finalize the setup process."""
        if request.user.tfa_enabled:
            return response.Response(status=404)
        device = request.user.totpdevice_set.first()
        if not device:
            return response.Response(status=404)
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(device.config_url, image_factory=factory)
        buf = io.BytesIO()
        img.save(buf)
        return response.Response(buf.getvalue(), content_type="application/xml")

    @extend_schema(
        request=core_v1_serializers.CheckTFASetupSerializer
    )
    @action(methods=["post"], detail=False, url_path="tfa/setup/check")
    def tfa_setup_check(self, request):
        """Check TFA setup."""
        serializer = core_v1_serializers.CheckTFASetupSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        # create static device for recovery purposes
        device = StaticDevice.objects.create(
            user=request.user,
            name="{} static device".format(request.user)
        )
        tokens = []
        for cpt in range(10):
            token = StaticToken.random_token()
            device.token_set.create(token=token)
            tokens.append(token)
        # Set enable flag to True so we can't go here anymore
        request.user.tfa_enabled = True
        request.user.save()
        # Generate new tokens
        device = request.user.totpdevice_set.first()
        refresh = RefreshToken.for_user(request.user)
        refresh[constants.TFA_DEVICE_TOKEN_KEY] = device.persistent_id
        return response.Response({
            "tokens": tokens,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering = ["-date_created"]
    ordering_fields = "__all__"
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.Log.objects.all()
    search_fields = ["logger", "level", "message"]
    serializer_class = serializers.LogSerializer


class LanguageViewSet(viewsets.ViewSet):
    """Language viewset."""

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def list(self, request, *args, **kwargs):
        languages = [
            {"code": lang[0], "label": lang[1]} for lang in constants.LANGUAGES
        ]
        return response.Response(languages)
