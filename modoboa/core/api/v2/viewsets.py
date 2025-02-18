"""Core API v2 viewsets."""

from django.utils.translation import gettext as _

from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.admin.api.v2 import serializers as admin_v2_serializers
from modoboa.core.api.v1 import serializers as core_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets
from modoboa.core.extensions import exts_pool
from modoboa.lib import pagination
from modoboa.lib.permissions import IsSuperUser
from modoboa.lib.throttle import GetThrottleViewsetMixin

import base64

from ... import constants
from ... import fido2_auth as f2_auth
from ... import models
from . import serializers


def create_static_tokens(request):
    """Utility function to create or recreate
    static tokens if needed."""
    device = request.user.staticdevice_set.first()
    if device is None:
        device = StaticDevice.objects.create(
            user=request.user, name=f"{request.user} static device"
        )
    elif device is not None:
        return None
    tokens = []
    for _cpt in range(10):
        token = StaticToken.random_token()
        device.token_set.create(token=token)
        tokens.append(token)
    return tokens


class AccountViewSet(core_v1_viewsets.AccountViewSet):
    """Account viewset."""

    @extend_schema(responses=admin_v2_serializers.AccountMeSerializer)
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
        if request.user.totp_enabled:
            return response.Response(status=404)
        device = request.user.totpdevice_set.first()
        if not device:
            return response.Response(status=404)
        return response.Response(
            {"key": base64.b32encode(device.bin_key), "url": device.config_url},
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
        tokens = create_static_tokens(request)
        # Set enable flag to True so we can't go here anymore
        request.user.totp_enabled = True
        request.user.save()
        if tokens is None:
            return response.Response(status=204)
        return response.Response({"tokens": tokens})

    @extend_schema(
        description="Get the list of available Modoboa applications for current user",
        responses={200: serializers.ModoboaApplicationSerializer},
    )
    @action(methods=["get"], detail=False)
    def available_applications(self, request):
        apps = []
        if request.user.role != "SimpleUsers":
            apps.append(
                {
                    "name": "admin",
                    "label": _("Administration"),
                    "icon": "mdi-toolbox",
                    "description": _("Administration console"),
                    "url": "/admin",
                }
            )
        apps += [
            {
                "name": "calendar",
                "label": _("Calendars"),
                "icon": "mdi-calendar",
                "description": _("Calendar"),
                "url": "/user/calendars",
            },
            {
                "name": "contacts",
                "label": _("Contacts"),
                "icon": "mdi-contacts-outline",
                "description": _("Address book"),
                "url": "/user/contacts",
            },
            # {
            #     "name": "webmail",
            #     "label": _("Webmail"),
            #     "icon": "mdi-at",
            #     "description": _("Webmail"),
            #     "url": "/user/webmail",
            # }
        ]
        apps += exts_pool.get_available_apps()
        serializer = serializers.ModoboaApplicationSerializer(apps, many=True)
        return response.Response(serializer.data)


class LogViewSet(GetThrottleViewsetMixin, viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering = ["-date_created"]
    ordering_fields = "__all__"
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (
        permissions.IsAuthenticated,
        IsSuperUser,
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
        if self.request.user.webauthn_enabled:
            return models.UserFidoKey.objects.filter(user=self.request.user)
        return None

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        queryset = self.get_queryset()
        to_save = False
        if not queryset.exists():
            request.user.webauthn_enabled = False
            to_save = True
        if not request.user.tfa_enabled:
            request.user.staticdevice_set.all().delete()
            to_save = True
        if to_save:
            request.user.save()
        return response.Response({"tfa_enabled": request.user.tfa_enabled})

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
        credential_data = f2_auth.end_registration(request)
        models.UserFidoKey.objects.create(
            name=request.data["name"],
            credential_data=credential_data,
            user=request.user,
        )
        if not request.user.webauthn_enabled:
            request.user.webauthn_enabled = True
            request.user.save()

        tokens = create_static_tokens(request)
        if tokens is not None:
            return response.Response({"tokens": tokens})
        return response.Response(status=204)
