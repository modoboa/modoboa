"""Admin API v2 viewsets."""

from django.utils.translation import ugettext as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from modoboa.admin.api.v1 import serializers as v1_serializers
from modoboa.lib import viewsets as lib_viewsets

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
    )
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
