"""Admin API."""

from django import http
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from django_filters import rest_framework as dj_filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, renderers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response

from modoboa.core import models as core_models
from modoboa.core import sms_backends
from modoboa.lib import renderers as lib_renderers
from modoboa.lib import viewsets as lib_viewsets

from ... import lib, models
from . import serializers


@extend_schema_view(
    retrieve=extend_schema(
        description="Retrieve a particular domain",
        summary="Retrieve a particular domain"
    ),
    list=extend_schema(
        description="Retrieve a list of domains",
        summary="Retrieve a list of domains"
    ),
    create=extend_schema(
        description="Create a new domain",
        summary="Create a new domain"
    )
)
class DomainViewSet(lib_viewsets.RevisionModelMixin, viewsets.ModelViewSet):
    """Domain viewset."""

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.DomainSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.Domain.objects.get_for_admin(self.request.user)

    def perform_destroy(self, instance):
        """Add custom args to delete call."""
        instance.delete(self.request.user)


class DomainAliasFilterSet(dj_filters.FilterSet):
    """Custom FilterSet for DomainAlias."""

    domain = dj_filters.CharFilter(field_name="target__name")

    class Meta:
        model = models.DomainAlias
        fields = ["domain"]


class DomainAliasViewSet(lib_viewsets.RevisionModelMixin,
                         lib_viewsets.ExpandableModelViewSet):
    """ViewSet for DomainAlias."""

    filter_backends = (dj_filters.DjangoFilterBackend, )
    filterset_class = DomainAliasFilterSet
    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    renderer_classes = (renderers.JSONRenderer, lib_renderers.CSVRenderer)
    serializer_expanded_fields = ["target"]
    serializer_class = serializers.DomainAliasSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        return models.DomainAlias.objects.get_for_admin(self.request.user)

    def get_renderer_context(self):
        context = super().get_renderer_context()
        context["headers"] = ["name", "target__name", "enabled"]
        return context


class AccountViewSet(lib_viewsets.RevisionModelMixin, viewsets.ModelViewSet):
    """ViewSet for User/Mailbox."""

    filter_backends = (filters.SearchFilter, )
    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    search_fields = ("^first_name", "^last_name", "^email")

    def get_serializer_class(self):
        """Return a serializer."""
        action_dict = {
            "list": serializers.AccountSerializer,
            "retrieve": serializers.AccountSerializer,
            "password": serializers.AccountPasswordSerializer,
            "reset_password": serializers.ResetPasswordSerializer,
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

    @action(methods=["put"], detail=True)
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

    @action(detail=False)
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

    @action(methods=["post"], detail=False)
    def reset_password(self, request):
        """Reset account password and send a new one by SMS."""
        sms_password_recovery = (
            request.localconfig.parameters
            .get_value("sms_password_recovery", app="core")
        )
        if not sms_password_recovery:
            return Response(status=404)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = core_models.User.objects.filter(
            email=serializer.validated_data["email"]).first()
        if not user or not user.phone_number:
            return Response(status=404)
        backend = sms_backends.get_active_backend(
            request.localconfig.parameters)
        if not backend:
            return Response(status=404)
        password = lib.make_password()
        content = _("Here is your new Modoboa password: {}").format(
            password)
        if not backend.send(content, [str(user.phone_number)]):
            body = {"status": "ko"}
        else:
            # SMS was sent, now we can set the new password.
            body = {"status": "ok"}
            user.set_password(password)
            user.save(update_fields=["password"])
        return Response(body)


class AliasViewSet(lib_viewsets.RevisionModelMixin, viewsets.ModelViewSet):
    """
    create:
    Create a new alias instance.
    """

    permission_classes = [IsAuthenticated, DjangoModelPermissions, ]
    serializer_class = serializers.AliasSerializer

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


class SenderAddressViewSet(lib_viewsets.RevisionModelMixin,
                           viewsets.ModelViewSet):
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
