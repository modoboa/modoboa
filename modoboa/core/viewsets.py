"""Core viewsets."""

from rest_framework import permissions, viewsets

from . import models
from . import serializers


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.Log.objects.all()
    serializer_class = serializers.LogSerializer
