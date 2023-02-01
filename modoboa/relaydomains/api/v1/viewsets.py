"""RelayDomain viewsets."""

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from modoboa.admin import models as admin_models
from modoboa.lib.throttle import UserLesserDdosUser
from modoboa.lib.viewsets import RevisionModelMixin
from . import serializers


class RelayDomainViewSet(RevisionModelMixin, viewsets.ModelViewSet):
    """RelayDomain viewset."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.RelayDomainSerializer

    def get_throttles(self):
        if self.action:
            self.throttle_classes.append(UserLesserDdosUser)
        return super().get_throttles()


    def get_queryset(self):
        """Filter queryset based on current user."""
        return (
            admin_models.Domain.objects.get_for_admin(self.request.user)
            .filter(type="relaydomain")
        )

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)
