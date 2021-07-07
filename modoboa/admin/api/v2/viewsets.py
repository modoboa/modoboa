"""Admin API v2 viewsets."""

from django.utils.translation import ugettext as _

from django.contrib.contenttypes.models import ContentType

from django_filters import rest_framework as dj_filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import (
    filters, mixins, permissions, response, status, viewsets
)
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from modoboa.admin.api.v1 import (
    serializers as v1_serializers, viewsets as v1_viewsets
)
from modoboa.core import models as core_models
from modoboa.lib import viewsets as lib_viewsets

from ... import lib
from ... import models
from . import serializers


@extend_schema_view(
    retrieve=extend_schema(
        description="Retrieve a particular domain",
        summary="Retrieve a particular domain"
    ),
    list=extend_schema(
        description="Retrieve a list of domains",
        summary="Retrieve a list of domains"
    ),
    create=extend_schema(
        description="Create a new domain",
        summary="Create a new domain"
    ),
    delete=extend_schema(
        description="Delete a particular domain",
        summary="Delete a particular domain"
    ),
)
class DomainViewSet(lib_viewsets.RevisionModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    """V2 viewset."""

    permission_classes = (
        permissions.IsAuthenticated, permissions.DjangoModelPermissions,
    )

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Domain.objects.get_for_admin(self.request.user)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "create":
            return serializers.DomainSerializer
        if self.action == "delete":
            return serializers.DeleteDomainSerializer
        if self.action == "administrators":
            return serializers.DomainAdminSerializer
        if self.action in ["add_administrator", "remove_administrator"]:
            return serializers.SimpleDomainAdminSerializer
        return v1_serializers.DomainSerializer

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


class AccountFilterSet(dj_filters.FilterSet):
    """Custom FilterSet for Account."""

    domain = dj_filters.ModelChoiceFilter(
        queryset=lambda request: models.Domain.objects.get_for_admin(
            request.user),
        field_name="mailbox__domain"
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
        return super().get_serializer_class()

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = (
            user.objectaccess_set
            .filter(content_type=ContentType.objects.get_for_model(user))
            .values_list("object_id", flat=True)
        )
        return core_models.User.objects.filter(pk__in=ids)

    @action(methods=["post"], detail=False)
    def validate(self, request, **kwargs):
        """Validate given account without creating it."""
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
            partial=True)
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


class IdentityViewSet(viewsets.ViewSet):
    """Viewset for identities."""

    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = None

    def list(self, request, **kwargs):
        """Return all identities."""
        serializer = serializers.IdentitySerializer(
            lib.get_identities(request.user), many=True)
        return response.Response(serializer.data)


class AliasViewSet(v1_viewsets.AliasViewSet):
    """Viewset for Alias."""

    serializer_class = serializers.AliasSerializer

    @action(methods=["post"], detail=False)
    def validate(self, request, **kwargs):
        """Validate given alias without creating it."""
        serializer = self.get_serializer(
            data=request.data,
            context=self.get_serializer_context(),
            partial=True)
        serializer.is_valid(raise_exception=True)
        return response.Response(status=204)

    @action(methods=["get"], detail=False)
    def random_address(self, request, **kwargs):
        return response.Response({
            "address": models.Alias.generate_random_address()
        })
