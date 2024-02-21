"""App. related viewsets."""

from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.admin import models as admin_models
from modoboa.lib.throttle import GetThrottleViewsetMixin

from ... import lib
from . import serializers


class DMARCViewSet(GetThrottleViewsetMixin, viewsets.GenericViewSet):

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Filter queryset based on current user."""
        return admin_models.Domain.objects.get_for_admin(self.request.user)

    @action(
        methods=["get"],
        detail=True,
        serializer_class=serializers.DMARCAligmentSerializer,
        url_path="dmarc/alignment_stats",
    )
    def alignment_stats(self, request, **kwargs):
        domain = self.get_object()
        if not domain.record_set.exists():
            return response.Response(status=204)
        try:
            stats = lib.get_aligment_stats(
                domain, self.request.query_params.get("period")
            )
        except ValueError:
            return response.Response("Invalid range received", status=400)
        serializer = self.get_serializer(stats)
        return response.Response(serializer.data)
