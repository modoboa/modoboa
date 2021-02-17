"""App. related viewsets."""

from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.admin import models as admin_models

from . import serializers


class DNSViewSet(viewsets.GenericViewSet):
    """A viewset to provide extra routes related to DNS information."""

    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        """Filter queryset based on current user."""
        return admin_models.Domain.objects.get_for_admin(self.request.user)

    @action(methods=["get"],
            detail=True,
            serializer_class=serializers.DNSDetailSerializer)
    def dns_detail(self, request, **kwargs):
        domain = self.get_object()
        serializer = self.get_serializer(domain)
        return response.Response(serializer.data)
