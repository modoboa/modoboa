"""Core API v2 viewsets."""

from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken

from modoboa.admin.api.v1 import serializers as admin_v1_serializers
from modoboa.core.api.v1 import viewsets as core_v1_viewsets
from modoboa.lib import pagination

from ... import constants
from ... import models
from . import serializers


class AccountViewSet(core_v1_viewsets.AccountViewSet):
    """Account viewset."""

    @action(methods=["get"], detail=False)
    @extend_schema(responses=admin_v1_serializers.AccountSerializer)
    def me(self, request):
        """Return information about connected user."""
        serializer = admin_v1_serializers.AccountSerializer(request.user)
        return response.Response(serializer.data)

    @action(methods=["post"], detail=False, url_path="tfa/verify")
    def tfa_verify_code(self, request):
        """Verify given code validity."""
        serializer = serializers.VerifyTFACodeSerializer(
            data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(request.user)
        refresh[constants.TFA_DEVICE_TOKEN_KEY] = (
            serializer.validated_data["code"].persistent_id)
        return response.Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """Log viewset."""

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering = ["-date_created"]
    ordering_fields = "__all__"
    pagination_class = pagination.CustomPageNumberPagination
    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )
    queryset = models.Log.objects.all()
    search_fields = ["logger", "level", "message"]
    serializer_class = serializers.LogSerializer
