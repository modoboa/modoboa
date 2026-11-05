"""Core API v2 viewsets."""

import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import gettext as _

from django_filters import rest_framework as dj_filters
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from reversion import revisions as reversion

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.admin.api.v2 import serializers as admin_v2_serializers
from modoboa.admin.models import Domain
from modoboa.core.api.v1 import serializers as core_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets
from modoboa.core.api.v1.viewsets import log_account_event
from modoboa.core.extensions import exts_pool
from modoboa.core.loggers import get_audit_actions
from modoboa.lib import pagination
from modoboa.lib import renderers as lib_renderers
from modoboa.lib.permissions import IsPrivilegedUser
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

    @extend_schema(
        responses=admin_v2_serializers.AccountMeSerializer,
        request=admin_v2_serializers.AccountMeUpdateSerializer,
    )
    @action(methods=["get", "put"], detail=False)
    def me(self, request):
        """Return information about connected user."""
        if request.method == "PUT":
            serializer = admin_v2_serializers.AccountMeUpdateSerializer(
                data=request.data, instance=request.user
            )
            serializer.is_valid(raise_exception=True)
            # Logged as a regular user modification (secondary email, phone...)
            with reversion.create_revision():
                instance = serializer.save()
            serializer = admin_v1_serializers.AccountSerializer(instance)
        else:
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

    @action(
        methods=["post"],
        detail=False,
        url_path="me/password/change",
        serializer_class=core_v1_serializers.AccountPasswordSerializer,
    )
    def set_me_password(self, request):
        serializer = core_v1_serializers.AccountPasswordSerializer(
            instance=request.user, data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_account_event(request, "core.password.changed", "changed their password")
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
            deleted, _details = Token.objects.filter(user=request.user).delete()
            if deleted:
                log_account_event(
                    request, "core.api_token.deleted", "deleted their API token"
                )
            return response.Response(status=204)
        status = 200
        if request.method == "POST":
            token, created = Token.objects.get_or_create(user=request.user)
            if created:
                status = 201
                log_account_event(
                    request, "core.api_token.created", "created an API token"
                )
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
        log_account_event(request, "core.tfa.totp_enabled", "enabled TOTP")
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
        if "modoboa.amavis" in settings.MODOBOA_APPS:
            apps.append(
                {
                    "name": "amavis",
                    "label": _("Quarantine"),
                    "icon": "mdi-server-security",
                    "description": _("Amavis quarantine"),
                    "url": "/user/quarantine",
                }
            )
        if hasattr(request.user, "mailbox"):
            if "modoboa.contacts" in settings.MODOBOA_APPS:
                apps += [
                    {
                        "name": "contacts",
                        "label": _("Contacts"),
                        "icon": "mdi-contacts-outline",
                        "description": _("Address book"),
                        "url": "/user/contacts",
                    }
                ]
            if "modoboa.calendars" in settings.MODOBOA_APPS:
                apps += [
                    {
                        "name": "calendar",
                        "label": _("Calendars"),
                        "icon": "mdi-calendar",
                        "description": _("Calendar"),
                        "url": "/user/calendars",
                    }
                ]
            if "modoboa.webmail" in settings.MODOBOA_APPS:
                apps += [
                    {
                        "name": "webmail",
                        "label": _("Webmail"),
                        "icon": "mdi-at",
                        "description": _("Webmail"),
                        "url": "/user/webmail",
                    }
                ]

        apps += exts_pool.get_available_apps()
        serializer = serializers.ModoboaApplicationSerializer(apps, many=True)
        return response.Response(serializer.data)


class LogFilterSet(dj_filters.FilterSet):
    """Audit trail filters. Dates are inclusive, in the server timezone."""

    date_from = dj_filters.DateFilter(
        field_name="date_created", lookup_expr="date__gte"
    )
    date_to = dj_filters.DateFilter(field_name="date_created", lookup_expr="date__lte")

    class Meta:
        model = models.Log
        fields = ["action", "actor_name", "domain", "level"]


class LogViewSet(GetThrottleViewsetMixin, viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    filter_backends = [
        filters.OrderingFilter,
        filters.SearchFilter,
        dj_filters.DjangoFilterBackend,
    ]
    filterset_class = LogFilterSet
    ordering = ["-date_created"]
    ordering_fields = "__all__"
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (permissions.IsAuthenticated, IsPrivilegedUser)
    # Only used by the router for URL names: see get_queryset()
    queryset = models.Log.objects.all()
    search_fields = [
        "logger",
        "level",
        "message",
        "actor_name",
        "domain",
        "object_repr",
    ]
    serializer_class = serializers.LogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return models.Log.objects.all()
        # Entries without domain (global parameters, superadmin logins...)
        # stay private to super administrators
        domains = Domain.objects.get_for_admin(user).values("name")
        return models.Log.objects.filter(domain__in=domains)

    @extend_schema(responses={(200, "text/csv"): str})
    @action(
        methods=["get"],
        detail=False,
        pagination_class=None,
        renderer_classes=(lib_renderers.CSVRenderer,),
    )
    def export(self, request):
        """Export the entries matching the filters, search and ordering."""
        labels = get_audit_actions()
        rows = [
            [
                "date",
                "level",
                "action",
                "label",
                "actor",
                "ip_address",
                "domain",
                "object_type",
                "object",
                "message",
                "details",
            ]
        ]
        queryset = self.filter_queryset(self.get_queryset()).select_related(
            "content_type"
        )
        # ponytail: the whole file is built in memory, like the other CSV
        # exports; switch to a StreamingHttpResponse if exports get too big.
        for log in queryset.iterator():
            ct = log.content_type
            rows.append(
                [
                    log.date_created.isoformat(),
                    log.level,
                    log.action,
                    labels.get(log.action, "") if log.action else "",
                    log.actor_name,
                    log.ip_address or "",
                    log.domain,
                    f"{ct.app_label}.{ct.model}" if ct else "",
                    log.object_repr,
                    log.message,
                    json.dumps(log.extra, cls=DjangoJSONEncoder) if log.extra else "",
                ]
            )
        return response.Response(rows)

    @extend_schema(responses=serializers.AuditActionSerializer(many=True))
    @action(methods=["get"], detail=False, pagination_class=None)
    def actions(self, request):
        """Return the catalog of audit actions, to build filters."""
        actions = [
            {"code": code, "label": label}
            for code, label in get_audit_actions().items()
        ]
        actions.sort(key=lambda item: item["label"])
        return response.Response(actions)


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

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        log_account_event(
            self.request,
            "core.tfa.fido_key_removed",
            f"removed security key '{instance.name}'",
        )

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
        key = models.UserFidoKey.objects.create(
            name=request.data["name"],
            credential_data=credential_data,
            user=request.user,
        )
        log_account_event(
            request, "core.tfa.fido_key_added", f"added security key '{key.name}'"
        )
        if not request.user.webauthn_enabled:
            request.user.webauthn_enabled = True
            request.user.save()

        tokens = create_static_tokens(request)
        if tokens is not None:
            return response.Response({"tokens": tokens})
        return response.Response(status=204)
