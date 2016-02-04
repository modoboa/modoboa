"""Admin API."""

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from . import models
from . import serializers


class DomainViewSet(viewsets.ModelViewSet):
    """ViewSet for Domain."""

    permission_classes = [DjangoModelPermissions, ]
    serializer_class = serializers.DomainSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Domain.objects.get_for_admin(self.request.user)

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)
