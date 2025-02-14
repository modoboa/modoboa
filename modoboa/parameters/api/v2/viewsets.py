"""Parameters viewsets."""

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.lib.permissions import IsSuperUser
from modoboa.lib.throttle import GetThrottleViewsetMixin

from . import serializers
from ... import tools


class BaseParametersViewSet(GetThrottleViewsetMixin, viewsets.ViewSet):
    """Parameter viewset."""

    level: str
    lookup_value_regex = r"\w+"
    serializer_class = None

    @extend_schema(responses=serializers.ApplicationSerializer(many=True))
    @action(methods=["get"], detail=False)
    def applications(self, request):
        """Return the list of registered applications."""
        applications = tools.registry.get_applications(self.level)
        return response.Response(applications)

    @extend_schema(responses=serializers.ParameterSerializer(many=True))
    @action(methods=["get"], detail=False)
    def structure(self, request):
        """Return parameter schema."""
        app = request.GET.get("app")
        data = tools.registry.get_structure(self.level, app)
        return response.Response(data)

    def _get_parameter_values(self, request, app: str) -> dict:
        raise NotImplementedError

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="A registered application name",
                type=str,
                required=True,
            ),
        ],
        responses=serializers.AppParametersSerializer,
    )
    def retrieve(self, request, pk: str):
        """Return all parameters for given app."""
        parameters = self._get_parameter_values(request, pk)
        serializer = tools.registry.get_serializer_class(self.level, pk)(parameters)
        result = serializers.AppParametersSerializer(
            {
                "label": tools.registry.get_label(self.level, pk),
                "params": serializer.data,
            }
        )
        return response.Response(result.data)

    def _save_parameter_values(self, request, app: str, data: dict) -> None:
        raise NotImplementedError

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="A registered application name",
                type=str,
                required=True,
            ),
        ]
    )
    def update(self, request, pk: str):
        """Save parameters for given app."""
        serializer = tools.registry.get_serializer_class(self.level, pk)(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        self._save_parameter_values(request, pk, serializer.validated_data)
        if hasattr(serializer, "post_save"):
            serializer.post_save(request)
        return response.Response()


class GlobalParametersViewSet(BaseParametersViewSet):
    """Parameter viewset, global level."""

    level = "global"
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]

    def _get_parameter_values(self, request, app: str) -> dict:
        return request.localconfig.parameters.get_values_dict(app)

    def _save_parameter_values(self, request, app: str, data: dict) -> None:
        request.localconfig.parameters.set_values(data, app=app)
        request.localconfig.save(update_fields=["_parameters"])


class UserParametersViewSet(BaseParametersViewSet):
    """Parameter viewset, user level."""

    level = "user"
    permission_classes = [permissions.IsAuthenticated]

    def _get_parameter_values(self, request, app: str) -> dict:
        return request.user.parameters.get_values_dict(app)

    def _save_parameter_values(self, request, app: str, data: dict) -> None:
        request.user.parameters.set_values(data, app=app)
        request.user.save(update_fields=["_parameters"])
