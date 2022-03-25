"""Transport related viewsets."""

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, response, viewsets

from . import serializers
from ... import backends


class TransportViewSet(viewsets.ViewSet):
    """Viewset for Transport."""

    permissions = (permissions.IsAuthenticated, )

    @extend_schema(
        responses={200: serializers.TransportBackendSerializer}
    )
    def list(self, request, *args, **kwargs):
        """Return the list of all defined transport backends."""
        all_settings = backends.manager.get_all_backend_settings()
        result = []
        for name, settings in all_settings.items():
            serializer = serializers.TransportBackendSerializer(
                {"name": name, "settings": settings}
            )
            result.append(serializer.data)
        return response.Response(result)
