"""Core API v2 viewsets."""

from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets

from ... import models
from . import serializers


class AccountViewSet(core_v1_viewsets.AccountViewSet):
    """Account viewset."""

    @action(methods=["get"], detail=False)
    def me(self, request):
        """Return information about connected user."""
        serializer = admin_v1_serializers.AccountSerializer(request.user)
        return response.Response(serializer.data)


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.Log.objects.all()
    serializer_class = serializers.LogSerializer
