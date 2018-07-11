# -*- coding: utf-8 -*-

"""Admin API."""

from __future__ import unicode_literals

from django import http
from django.contrib.contenttypes.models import ContentType

from rest_framework import filters, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import ParseError
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response

from modoboa.core import models as core_models
from . import models, serializers


class DomainViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given domain.

    list:
    Return a list of all existing domains.

    create:
    Create a new domain instance.
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.DomainSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Domain.objects.get_for_admin(self.request.user)

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)


class DomainAliasViewSet(viewsets.ModelViewSet):
    """ViewSet for DomainAlias."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.DomainAliasSerializer
    http_method_names = ["get", "post", "put", "delete"]

    def get_queryset(self):
        """Filter queryset based on current user."""
        queryset = models.DomainAlias.objects.get_for_admin(self.request.user)
        domain = self.request.query_params.get("domain")
        if domain:
            queryset = queryset.filter(target__name=domain)
        return queryset


class AccountViewSet(viewsets.ModelViewSet):
    """ViewSet for User/Mailbox."""

    filter_backends = [filters.SearchFilter]
    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    search_fields = ("^first_name", "^last_name", "^email")

    def get_serializer_class(self):
        """Return a serializer."""
        action_dict = {
            "list": serializers.AccountSerializer,
            "retrieve": serializers.AccountSerializer,
            "password": serializers.AccountPasswordSerializer
        }
        return action_dict.get(
            self.action, serializers.WritableAccountSerializer)

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = user.objectaccess_set \
            .filter(content_type=ContentType.objects.get_for_model(user)) \
            .values_list("object_id", flat=True)
        queryset = core_models.User.objects.filter(pk__in=ids)
        domain = self.request.query_params.get("domain")
        if domain:
            queryset = queryset.filter(mailbox__domain__name=domain)
        return queryset

    @detail_route(methods=["put"])
    def password(self, request, pk=None):
        """Change account password."""
        try:
            user = core_models.User.objects.get(pk=pk)
        except core_models.User.DoesNotExist:
            raise http.Http404
        serializer = self.get_serializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response()
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @list_route()
    def exists(self, request):
        """Check if account exists.

        Requires a valid email address as argument. Example:

        GET /exists/?email=user@test.com

        """
        email = request.GET.get("email")
        if not email:
            raise ParseError("email not provided")
        if not core_models.User.objects.filter(email=email).exists():
            data = {"exists": False}
        else:
            data = {"exists": True}
        serializer = serializers.AccountExistsSerializer(data)
        return Response(serializer.data)


class AliasViewSet(viewsets.ModelViewSet):
    """
    create:
    Create a new alias instance.
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.AliasSerializer
    http_method_names = ["get", "post", "put", "delete"]

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        ids = (
            user.objectaccess_set.filter(
                content_type=ContentType.objects.get_for_model(models.Alias))
            .values_list("object_id", flat=True)
        )
        queryset = models.Alias.objects.filter(pk__in=ids)
        domain = self.request.query_params.get("domain")
        if domain:
            queryset = queryset.filter(domain__name=domain)
        return queryset


class SenderAddressViewSet(viewsets.ModelViewSet):
    """View set for SenderAddress model."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.SenderAddressSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        user = self.request.user
        mb_ids = (
            user.objectaccess_set.filter(
                content_type=ContentType.objects.get_for_model(models.Mailbox))
            .values_list("object_id", flat=True)
        )
        return models.SenderAddress.objects.filter(mailbox__pk__in=mb_ids)
