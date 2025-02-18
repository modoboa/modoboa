"""Viewsets for API V2 for imap_migration."""

import imaplib
import ssl

from rest_framework import response, filters, mixins, permissions, viewsets
from rest_framework.decorators import action

from modoboa.lib.throttle import GetThrottleViewsetMixin

from ... import models
from . import serializers


class EmailProviderViewSet(GetThrottleViewsetMixin, viewsets.ModelViewSet):
    """ViewSet class for EmailProvider."""

    filter_backends = (filters.SearchFilter,)
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.EmailProvider.objects.all().prefetch_related("domains")
    search_fields = ("name",)
    serializer_class = serializers.EmailProviderSerializer

    @action(methods=["post"], detail=False)
    def check_connection(self, request, **kwargs):
        """check that provided information allow connection to imap server."""
        serializer = serializers.CheckProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        secured = serializer.data["secured"]
        address = serializer.data["address"]
        port = serializer.data["port"]
        try:
            if secured:
                imaplib.IMAP4_SSL(address, port)
            else:
                imaplib.IMAP4(address, port)
        except (OSError, imaplib.IMAP4.error, ssl.SSLError):
            return response.Response({"status": "failed"}, 400)
        return response.Response(status=200)

    @action(methods=["post"], detail=False)
    def check_associated_domain(self, request, **kwargs):
        """check that the associated domain is either the same as the provider,
        or if a local domain already exists.
        This is to prevent errros on setup."""
        serializer = serializers.CheckAssociatedDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response.Response(status=200)


class MigrationViewSet(
    GetThrottleViewsetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet class for Migration."""

    filter_backends = (filters.SearchFilter,)
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.Migration.objects.all().select_related(
        "provider", "mailbox__domain"
    )
    search_fields = (
        "username",
        "provider__name",
        "mailbox__address",
        "mailbox__domain__name",
    )
    serializer_class = serializers.MigrationSerializer
