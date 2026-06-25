"""Viewsets for API V2 for imap_migration."""

import imaplib
import ssl

from rest_framework import response, filters, mixins, permissions, viewsets
from rest_framework.decorators import action

from modoboa.admin import models as admin_models
from modoboa.lib.permissions import IsPrivilegedUser
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

    def get_queryset(self):
        """Restrict providers to those the current user is allowed to see."""
        user = self.request.user
        qset = super().get_queryset()
        if user.role == "SuperAdmins":
            return qset
        if user.role in ("DomainAdmins", "Resellers"):
            domains = admin_models.Domain.objects.get_for_admin(user)
            return qset.filter(domains__new_domain__in=domains).distinct()
        # SimpleUsers have no business listing migration providers.
        return qset.none()

    def get_permissions(self):
        """The setup-only actions must stay out of reach of simple users."""
        if self.action in ("check_connection", "check_associated_domain"):
            return [permissions.IsAuthenticated(), IsPrivilegedUser()]
        return super().get_permissions()

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

    def get_queryset(self):
        """Restrict migrations to those the current user is allowed to see."""
        user = self.request.user
        qset = super().get_queryset()
        if user.role == "SuperAdmins":
            return qset
        if user.role == "SimpleUsers":
            return qset.filter(mailbox__user=user)
        if user.role in ("DomainAdmins", "Resellers"):
            mailboxes = admin_models.Mailbox.objects.get_for_admin(user)
            return qset.filter(mailbox__in=mailboxes)
        return qset.none()
