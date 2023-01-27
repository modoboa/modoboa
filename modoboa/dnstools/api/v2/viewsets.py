"""App. related viewsets."""

from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action
from rest_framework.throttling import UserRateThrottle

from modoboa.admin import models as admin_models
from modoboa.lib.throttle import UserDdosPerView

from . import serializers


class DNSViewSet(viewsets.GenericViewSet):
    """A viewset to provide extra routes related to DNS information."""

    permission_classes = (permissions.IsAuthenticated, )
    throttle_classes = [UserDdosPerView, UserRateThrottle]

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
