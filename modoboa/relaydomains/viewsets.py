"""RelayDomain viewsets."""

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

from modoboa.admin import models as admin_models
from . import serializers


class RelayDomainViewSet(viewsets.ModelViewSet):
    """RelayDomain viewset."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.RelayDomainSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return (
            admin_models.Domain.objects.get_for_admin(self.request.user)
            .filter(type="relaydomain")
        )

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)
