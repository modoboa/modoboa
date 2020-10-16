"""Parameters viewsets."""

from rest_framework import response, viewsets
from rest_framework.decorators import action

from . import tools


class ParametersViewSet(viewsets.ViewSet):
    """Parameter viewset."""

    lookup_value_regex = r"\w+"

    @action(methods=["get"], detail=False)
    def applications(self, request):
        """Return application list."""
        applications = tools.registry.get_applications("global")
        return response.Response(applications)

    @action(methods=["get"], detail=False)
    def structure(self, request):
        """Return parameter schema."""
        app = request.GET.get("app")
        data = tools.registry.get_structure("global", app)
        return response.Response(data)

    def retrieve(self, request, pk):
        """Return all parameters for given app."""
        parameters = request.localconfig.parameters.get_values_dict(pk)
        serializer = tools.registry.get_serializer_class("global", pk)(
            parameters)
        return response.Response(serializer.data)

    def update(self, request, pk):
        """Save parameters for given app."""
        serializer = tools.registry.get_serializer_class("global", pk)(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        request.localconfig.parameters.set_values(
            serializer.validated_data, app=pk)
        request.localconfig.save(update_fields=["_parameters"])
        return response.Response()
