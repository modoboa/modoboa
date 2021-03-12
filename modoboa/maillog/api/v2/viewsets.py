"""App. related viewsets."""

import time

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, response, viewsets

from ... import signals
from . import serializers


class StatisticsViewSet(viewsets.ViewSet):
    """A viewset to provide extra route related to mail statistics."""

    permission_classes = (permissions.IsAuthenticated, )

    @extend_schema(
        parameters=[serializers.StatisticsInputSerializer],
        responses={200: serializers.StatisticsSerializer}
    )
    def list(self, request, **kwargs):
        serializer = serializers.StatisticsInputSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        graph_sets = {}
        for result in signals.get_graph_sets.send(
                sender="index", user=request.user):
            graph_sets.update(result[1])
        gset = serializer.validated_data["gset"]
        fname = graph_sets[gset].get_file_name(
            request.user, serializer.validated_data.get("searchquery"))
        period = serializer.validated_data["period"]
        if period == "custom":
            start = int(
                time.mktime(serializer.validated_data["start"].timetuple())
            )
            end = int(
                time.mktime(serializer.validated_data["end"].timetuple())
            )
        else:
            end = int(time.mktime(time.localtime()))
            start = "-1{}".format(period)
        graphs = graph_sets[gset].export(
            fname, start, end, serializer.validated_data.get("graphic")
        )
        return response.Response({"graphs": graphs})
