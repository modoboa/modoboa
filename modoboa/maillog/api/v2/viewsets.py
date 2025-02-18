"""App. related viewsets."""

import time

from django.db.models import Q

from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, response, viewsets

from modoboa.admin import models as admin_models
from modoboa.lib import pagination
from modoboa.lib.throttle import GetThrottleViewsetMixin

from ... import models
from ... import signals
from . import serializers


class StatisticsViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """A viewset to provide extra route related to mail statistics."""

    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        parameters=[serializers.StatisticsInputSerializer],
        responses={200: serializers.StatisticsSerializer},
    )
    def list(self, request, **kwargs):
        serializer = serializers.StatisticsInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        graph_sets = {}
        for result in signals.get_graph_sets.send(sender="index", user=request.user):
            graph_sets.update(result[1])
        gset = serializer.validated_data["gset"]
        fname = graph_sets[gset].get_file_name(
            request.user, serializer.validated_data.get("searchquery")
        )
        period = serializer.validated_data["period"]
        if period == "custom":
            start = int(time.mktime(serializer.validated_data["start"].timetuple()))
            end = int(time.mktime(serializer.validated_data["end"].timetuple()))
        else:
            end = int(time.mktime(time.localtime()))
            start = f"-1{period}"
        graphs = graph_sets[gset].export(
            fname, start, end, serializer.validated_data.get("graphic")
        )
        return response.Response({"graphs": graphs})


class MaillogViewSet(GetThrottleViewsetMixin, viewsets.ReadOnlyModelViewSet):
    """Simple viewset to access message log."""

    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering = ["-date"]
    ordering_fields = "__all__"
    pagination_class = pagination.CustomPageNumberPagination
    permissions = (permissions.IsAuthenticated,)
    search_fields = ["queue_id", "sender", "rcpt", "original_rcpt", "status"]
    serializer_class = serializers.MaillogSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        domains = admin_models.Domain.objects.get_for_admin(self.request.user)
        return models.Maillog.objects.filter(
            Q(from_domain__in=domains) | Q(to_domain__in=domains)
        )
