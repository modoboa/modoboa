"""API viewsets."""

from rest_framework import filters, mixins, permissions, viewsets

from modoboa.lib.throttle import GetThrottleViewsetMixin

from ... import models
from . import serializers


class EmailProviderViewSet(GetThrottleViewsetMixin, viewsets.ModelViewSet):
    """ViewSet class for EmailProvider."""

    filter_backends = (filters.SearchFilter, )
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    )
    queryset = models.EmailProvider.objects.all().prefetch_related("domains")
    search_fields = ("name", )
    serializer_class = serializers.EmailProviderSerializer


class MigrationViewSet(GetThrottleViewsetMixin,
                       mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """ViewSet class for Migration."""

    filter_backends = (filters.SearchFilter, )
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions
    )
    queryset = models.Migration.objects.all().select_related(
        "provider", "mailbox__domain")
    search_fields = (
        "username", "provider__name", "mailbox__address",
        "mailbox__domain__name")
    serializer_class = serializers.MigrationSerializer
