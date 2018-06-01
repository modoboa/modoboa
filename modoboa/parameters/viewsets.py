"""Parameters viewsets."""

from rest_framework import decorators, response, viewsets

from . import serializers
from . import tools


class ParametersViewSet(viewsets.ViewSet):
    """Parameter viewset."""

    @decorators.list_route(methods=["get"])
    def structure(self, request):
        """Return parameter schema."""
        data = tools.registry.get_structure("global")
        return response.Response(data)

    def list(self, request):
        """Return all parameters."""
        parameters = request.localconfig.parameters.get_values_dict("core")
        serializer = serializers.ParametersSerializer(data=parameters)
        serializer.is_valid(raise_exception=True)
        return response.Response(serializer.validated_data)
