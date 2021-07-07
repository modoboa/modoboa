"""Parameters viewsets."""

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import response, viewsets
from rest_framework.decorators import action

from . import serializers
from ... import tools


class ParametersViewSet(viewsets.ViewSet):
    """Parameter viewset."""

    lookup_value_regex = r"\w+"
    serializer_class = None

    @extend_schema(responses=serializers.ApplicationSerializer(many=True))
    @action(methods=["get"], detail=False)
    def applications(self, request):
        """Return the list of registered applications."""
        applications = tools.registry.get_applications("global")
        return response.Response(applications)

    @extend_schema(responses=serializers.ParameterSerializer(many=True))
    @action(methods=["get"], detail=False)
    def structure(self, request):
        """Return parameter schema."""
        app = request.GET.get("app")
        data = tools.registry.get_structure("global", app)
        return response.Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='id', location=OpenApiParameter.PATH,
                description='A registered application name',
                type=str, required=True
            ),
        ]
    )
    def retrieve(self, request, pk: str):
        """Return all parameters for given app."""
        parameters = request.localconfig.parameters.get_values_dict(pk)
        serializer = tools.registry.get_serializer_class("global", pk)(
            parameters)
        return response.Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='id', location=OpenApiParameter.PATH,
                description='A registered application name',
                type=str, required=True
            ),
        ]
    )
    def update(self, request, pk: str):
        """Save parameters for given app."""
        serializer = tools.registry.get_serializer_class("global", pk)(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        request.localconfig.parameters.set_values(
            serializer.validated_data, app=pk)
        request.localconfig.save(update_fields=["_parameters"])
        return response.Response()
