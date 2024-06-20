"""Core API v2 viewsets."""

from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.core.api.v1 import serializers as core_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets
from modoboa.lib import pagination
from modoboa.lib.throttle import GetThrottleViewsetMixin

from ... import constants
from ... import fido2_auth as f2_auth
from ... import models
from . import serializers


class AccountViewSet(core_v1_viewsets.AccountViewSet):
    """Account viewset."""

    @extend_schema(responses=admin_v1_serializers.AccountSerializer)
    @action(methods=["get"], detail=False)
    def me(self, request):
        """Return information about connected user."""
        serializer = admin_v1_serializers.AccountSerializer(request.user)
        return response.Response(serializer.data)

    @action(
        methods=["post"],
        detail=False,
        url_path="me/password",
        serializer_class=serializers.CheckPasswordSerializer,
    )
    def check_me_password(self, request):
        """Check current user password."""
        serializer = serializers.CheckPasswordSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        return response.Response()

    @extend_schema(
        description="Get current API token",
        responses={200: serializers.UserAPITokenSerializer},
        methods=["GET"],
    )
    @extend_schema(
        description="Generate new API token",
        responses={201: serializers.UserAPITokenSerializer},
        methods=["POST"],
    )
    @extend_schema(description="Delete current API token", methods=["DELETE"])
    @action(
        methods=["get", "post", "delete"],
        detail=False,
        url_path="api_token",
    )
    def manage_api_token(self, request):
        """Manage API token."""
        if not request.user.is_superuser:
            raise PermissionDenied("Only super administrators can have API tokens")
        if request.method == "DELETE":
            Token.objects.filter(user=request.user).delete()
            return response.Response(status=204)
        status = 200
        if request.method == "POST":
            token, created = Token.objects.get_or_create(user=request.user)
            if created:
                status = 201
        else:
            if hasattr(request.user, "auth_token"):
                token = request.user.auth_token
            else:
                token = ""
        serializer = serializers.UserAPITokenSerializer({"token": str(token)})
        return response.Response(serializer.data, status=status)

    @action(methods=["get"], detail=False, url_path="tfa/setup/key")
    def tfa_setup_get_key(self, request):
        """Get a key and url to finalize the setup process."""
        if request.user.tfa_enabled:
            return response.Response(status=404)
        device = request.user.totpdevice_set.first()
        if not device:
            return response.Response(status=404)
        return response.Response(
            {"key": device.key, "url": device.config_url},
            content_type="application/json",
        )

    @extend_schema(request=core_v1_serializers.CheckTFASetupSerializer)
    @action(methods=["post"], detail=False, url_path="tfa/setup/check")
    def tfa_setup_check(self, request):
        """Check TFA setup."""
        serializer = core_v1_serializers.CheckTFASetupSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        # create static device for recovery purposes
        device = StaticDevice.objects.create(
            user=request.user, name="{} static device".format(request.user)
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
        # refresh = RefreshToken.for_user(request.user)
        # refresh[constants.TFA_DEVICE_TOKEN_KEY] = device.persistent_id
        return response.Response(
            {
                "tokens": tokens,
                # "refresh": str(refresh),
                # "access": str(refresh.access_token),
            }
        )


class LogViewSet(GetThrottleViewsetMixin, viewsets.ReadOnlyModelViewSet):
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


class LanguageViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """Language viewset."""

    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        languages = [
            {"code": lang[0], "label": lang[1]} for lang in constants.LANGUAGES
        ]
        return response.Response(languages)


class FIDOViewSet(
    GetThrottleViewsetMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Fido management viewset."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.FIDOSerializer

    def get_queryset(self):
        return models.UserFidoKeys.objects.filter(user=self.request.user)

    @action(methods=["post"], detail=False, url_path="registration/begin")
    def registration_begin(self, request):
        """An Api View which starts the registration process of a fido key."""
        options = f2_auth.begin_registration(request)
        return response.Response(dict(options))

    @action(methods=["post"], detail=False, url_path="registration/end")
    def registration_end(self, request):
        """An Api View to complete the registration process of a fido key."""
        serializer = serializers.FidoRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credential_data = f2_auth.end_registration(
            request.data, request.session.pop("fido2_state"), request.user.id
        )
        models.UserFidoKeys.objects.create(
            name=request.data["name"],
            credential_data=credential_data,
            user=request.user,
        )
        if not request.user.tfa_enabled:
            request.user.tfa_enabled = True
            request.user.save()
        return response.Response(status=204)
