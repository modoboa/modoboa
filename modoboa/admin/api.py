"""Admin API."""

from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

from modoboa.core import models as core_models

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


class AccountViewSet(viewsets.ModelViewSet):
    """ViewSet for User/Mailbox."""

    permission_classes = [DjangoModelPermissions, ]

    def get_serializer_class(self):
        """Return a serializer."""
        if self.request.method == "GET":
            return serializers.AccountSerializer
        return serializers.CreateAccountSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = user.objectaccess_set \
            .filter(content_type=ContentType.objects.get_for_model(user)) \
            .values_list('object_id', flat=True)
        return core_models.User.objects.filter(pk__in=ids)

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)
