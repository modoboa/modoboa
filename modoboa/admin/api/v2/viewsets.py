"""Admin API v2 viewsets."""

from django.utils.translation import gettext as _

from django.contrib.contenttypes.models import ContentType

from django_filters import rest_framework as dj_filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import (
    filters,
    mixins,
    parsers,
    permissions,
    response,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from modoboa.admin.api.v1 import viewsets as v1_viewsets
from modoboa.core import models as core_models
from modoboa.lib import pagination
from modoboa.lib import renderers as lib_renderers
from modoboa.lib import viewsets as lib_viewsets
from modoboa.lib.throttle import GetThrottleViewsetMixin
from modoboa.lib.exceptions import AliasExists

from ... import lib
from ... import models
from ... import constants
from . import serializers


@extend_schema_view(
    retrieve=extend_schema(
        description="Retrieve a particular domain",
        summary="Retrieve a particular domain",
    ),
    list=extend_schema(
        description="Retrieve a list of domains", summary="Retrieve a list of domains"
    ),
    create=extend_schema(
        description="Create a new domain", summary="Create a new domain"
    ),
    delete=extend_schema(
        description="Delete a particular domain", summary="Delete a particular domain"
    ),
)
class DomainViewSet(
    GetThrottleViewsetMixin,
    lib_viewsets.RevisionModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """V2 viewset."""

    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Domain.objects.get_for_admin(self.request.user)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "delete":
            return serializers.DeleteDomainSerializer
        if self.action == "administrators":
            return serializers.DomainAdminSerializer
        if self.action in ["add_administrator", "remove_administrator"]:
            return serializers.SimpleDomainAdminSerializer
        return serializers.DomainSerializer

    @action(methods=["post"], detail=True)
    def delete(self, request, **kwargs):
        """Custom delete method that accepts body arguments."""
        domain = self.get_object()
        if not request.user.can_access(domain):
            raise PermissionDenied(_("You don't have access to this domain"))
        mb = getattr(request.user, "mailbox", None)
        if mb and mb.domain == domain:
            raise PermissionDenied(_("You can't delete your own domain"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        domain.delete(request.user, serializer.validated_data["keep_folder"])
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=True)
    def administrators(self, request, **kwargs):
        """Retrieve all administrators of a domain."""
        domain = self.get_object()
        serializer = self.get_serializer(domain.admins, many=True)
        return response.Response(serializer.data)

    @action(methods=["post"], detail=True, url_path="administrators/add")
    def add_administrator(self, request, **kwargs):
        """Add an administrator to a domain."""
        domain = self.get_object()
        context = self.get_serializer_context()
        context["domain"] = domain
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        domain.add_admin(serializer.validated_data["account"])
        return response.Response()

    @action(methods=["post"], detail=True, url_path="administrators/remove")
    def remove_administrator(self, request, **kwargs):
        """Remove an administrator from a domain."""
        domain = self.get_object()
        context = self.get_serializer_context()
        context["domain"] = domain
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        domain.remove_admin(serializer.validated_data["account"])
        return response.Response()

    @action(
        methods=["get"], detail=False, renderer_classes=(lib_renderers.CSVRenderer,)
    )
    def export(self, request, **kwargs):
        """Export domains and aliases to CSV."""
        result = []
        for domain in self.get_queryset():
            result += domain.to_csv_rows()
        return response.Response(result)

    @extend_schema(request=serializers.CSVImportSerializer)
    @action(
        methods=["post"],
        detail=False,
        parser_classes=(parsers.MultiPartParser, parsers.FormParser),
        url_path="import",
    )
    def import_from_csv(self, request, **kwargs):
        """Import domains and aliases from CSV file."""
        serializer = serializers.CSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status, msg = lib.import_data(
            request.user, request.FILES["sourcefile"], serializer.validated_data
        )
        return response.Response({"status": status, "message": msg})


class AccountFilterSet(dj_filters.FilterSet):
    """Custom FilterSet for Account."""

    domain = dj_filters.ModelChoiceFilter(
        queryset=lambda request: models.Domain.objects.get_for_admin(request.user),
        field_name="mailbox__domain",
    )
    role = dj_filters.CharFilter(method="filter_role")

    class Meta:
        model = core_models.User
        fields = ["domain", "role"]

    def filter_role(self, queryset, name, value):
        return queryset.filter(groups__name=value)


class AccountViewSet(v1_viewsets.AccountViewSet):
    """ViewSet for User/Mailbox."""

    filter_backends = (filters.SearchFilter, dj_filters.DjangoFilterBackend)
    filterset_class = AccountFilterSet

    def get_serializer_class(self):
        if self.action in ["create", "validate", "update", "partial_update"]:
            return serializers.WritableAccountSerializer
        if self.action == "delete":
            return serializers.DeleteAccountSerializer
        if self.action in ["list", "retrieve"]:
            return serializers.AccountSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = user.objectaccess_set.filter(
            content_type=ContentType.objects.get_for_model(user)
        ).values_list("object_id", flat=True)
        return core_models.User.objects.filter(pk__in=ids).prefetch_related(
            "userobjectlimit_set"
        )

    @action(methods=["post"], detail=False)
    def validate(self, request, **kwargs):
        """Validate given account without creating it."""
        serializer = self.get_serializer(
            data=request.data, context=self.get_serializer_context(), partial=True
        )
        serializer.is_valid(raise_exception=True)
        return response.Response(status=204)

    @action(methods=["get"], detail=False)
    def random_password(self, request, **kwargs):
        """Generate a random password."""
        password = lib.make_password()
        return response.Response({"password": password})

    @action(methods=["post"], detail=True)
    def delete(self, request, **kwargs):
        """Custom delete method that accepts body arguments."""
        account = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class IdentityViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """Viewset for identities."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = None

    def list(self, request, **kwargs):
        """Return all identities."""
        serializer = serializers.IdentitySerializer(
            lib.get_identities(request.user), many=True
        )
        return response.Response(serializer.data)

    @action(
        methods=["get"], detail=False, renderer_classes=(lib_renderers.CSVRenderer,)
    )
    def export(self, request, **kwargs):
        """Export accounts and aliases to CSV."""
        result = []
        for idt in lib.get_identities(request.user):
            result.append(idt.to_csv_row())
        return response.Response(result)

    @extend_schema(request=serializers.CSVIdentityImportSerializer)
    @action(
        methods=["post"],
        detail=False,
        parser_classes=(parsers.MultiPartParser, parsers.FormParser),
        url_path="import",
    )
    def import_from_csv(self, request, **kwargs):
        """Import accounts and aliases from CSV file."""
        serializer = serializers.CSVIdentityImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status, msg = lib.import_data(
            request.user, request.FILES["sourcefile"], serializer.validated_data
        )
        return response.Response({"status": status, "message": msg})


class AliasViewSet(v1_viewsets.AliasViewSet):
    """Viewset for Alias."""

    serializer_class = serializers.AliasSerializer

    @action(methods=["post"], detail=False)
    def validate(self, request, **kwargs):
        """Validate given alias without creating it."""
        serializer = self.get_serializer(
            data=request.data, context=self.get_serializer_context(), partial=True
        )
        try:
            serializer.is_valid(raise_exception=True)
        except AliasExists as e:
            return response.Response(
                data={"id": e.alias_id, "status": _("This alias already exists")},
                status=409,
            )
        return response.Response(status=204)

    @action(methods=["get"], detail=False)
    def random_address(self, request, **kwargs):
        return response.Response({"address": models.Alias.generate_random_address()})


class UserAccountViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """Viewset for current user operations."""

    @action(methods=["get", "post"], detail=False)
    def forward(self, request, **kwargs):
        """Get or define user forward."""
        mb = request.user.mailbox
        alias = models.Alias.objects.filter(
            address=mb.full_address, internal=False
        ).first()
        data = {}
        if request.method == "GET":
            if alias is not None and alias.recipients:
                recipients = list(alias.recipients)
                if alias.aliasrecipient_set.filter(r_mailbox=mb).exists():
                    data["keepcopies"] = True
                    recipients.remove(mb.full_address)
                data["recipients"] = "\n".join(recipients)
            serializer = serializers.UserForwardSerializer(data)
            return response.Response(serializer.data)
        serializer = serializers.UserForwardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients = serializer.validated_data.get("recipients")
        if not recipients:
            models.Alias.objects.filter(
                address=mb.full_address, internal=False
            ).delete()
            # Make sure internal self-alias is enabled
            models.Alias.objects.filter(address=mb.full_address, internal=True).update(
                enabled=True
            )
        else:
            if alias is None:
                alias = models.Alias.objects.create(
                    address=mb.full_address, domain=mb.domain, enabled=mb.user.is_active
                )
                alias.post_create(request.user)
            if serializer.validated_data["keepcopies"]:
                # Make sure internal self-alias is enabled
                models.Alias.objects.filter(
                    address=mb.full_address, internal=True
                ).update(enabled=True)
                recipients.append(mb.full_address)
            else:
                # Deactivate internal self-alias to avoid storing
                # local copies...
                models.Alias.objects.filter(
                    address=mb.full_address, internal=True
                ).update(enabled=False)
            alias.set_recipients(recipients)
        return response.Response(serializer.validated_data)


class AlarmFilterSet(dj_filters.FilterSet):
    """Custom FilterSet for Alarms."""

    min_date = dj_filters.DateTimeFilter(method="filter_date")

    class Meta:
        model = models.Alarm
        fields = ["created"]

    def filter_date(self, queryset, name, value):
        return queryset.filter(created__gt=value)


class AlarmViewSet(
    GetThrottleViewsetMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset for Alarm."""

    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
        dj_filters.DjangoFilterBackend,
    )
    filterset_class = AlarmFilterSet
    ordering_fields = ["created", "status", "title"]
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (permissions.IsAuthenticated,)
    search_fields = ["domain__name", "title"]
    serializer_class = serializers.AlarmSerializer

    def get_queryset(self):
        return (
            models.Alarm.objects.select_related("domain")
            .filter(domain__in=models.Domain.objects.get_for_admin(self.request.user))
            .order_by("-created")
        )

    @action(methods=["patch"], detail=True)
    def switch(self, request, **kwargs):
        """Custom update method that switch status of an alarm."""
        alarm = self.get_object()
        serializer = serializers.AlarmSwitchStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.data["status"] == constants.ALARM_CLOSED:
            alarm.close()
        else:
            alarm.reopen()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["delete"], detail=False)
    def bulk_delete(self, request, **kwargs):
        """Delete multiple alarms at the same time."""
        ids = request.query_params.getlist("ids[]")
        if not ids:
            return response.Response(_("No alarm ID provided"), status=400)
        try:
            ids = [int(alarm_id) for alarm_id in ids]
        except ValueError:
            return response.Response(_("Received invalid alarm id(s)"), status=400)
        models.Alarm.objects.filter(pk__in=ids).delete()
        return response.Response(status=204)
