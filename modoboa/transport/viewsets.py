"""Transport viewsets."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions

from . import models
from . import serializers


class TransportViewSet(viewsets.ModelViewSet):
    """Transport viewset."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.TransportSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Transport.objects.get_for_admin(self.request.user)
