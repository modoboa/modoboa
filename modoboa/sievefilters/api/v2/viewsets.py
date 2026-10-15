"""Sievefilters viewsets."""

import copy

from sievelib.commands import BadArgument, BadValue
from sievelib.factory import FilterAlreadyExists

from django.http import HttpResponse
from django.utils.translation import gettext as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, response, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from modoboa.lib.oauth2 import get_access_token
from modoboa.lib.viewsets import HasMailbox
from modoboa.sievefilters import constants
from modoboa.sievefilters.lib import (
    SieveClient,
    SieveClientError,
    SieveScriptParseError,
    UnsupportedSieveFilter,
)
from modoboa.sievefilters.rfc6266 import build_header
from modoboa.sievefilters.api.v2 import serializers


FILTER_SET_ID = OpenApiParameter(
    "id",
    OpenApiTypes.STR,
    description="Name of an existing filter set",
    location=OpenApiParameter.PATH,
)


class FilterSetViewSet(viewsets.ViewSet):
    permission_classes = (
        permissions.IsAuthenticated,
        HasMailbox,
    )
    serializer_class = serializers.FilterSetSerializer
    lookup_value_regex = "[^/]+"

    FORBIDDEN_NAME_CHARS = constants.FORBIDDEN_NAME_CHARS

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        for key in ("pk", "filter"):
            value = kwargs.get(key)
            if value is None:
                continue
            if any(c in value for c in self.FORBIDDEN_NAME_CHARS):
                raise DRFValidationError({key: _("Name contains forbidden characters")})

    sclient: SieveClient | None = None

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            if self.sclient:
                self.sclient.logout()

    def get_sieve_client(self, request):
        self.sclient = SieveClient(
            user=request.user.username, password=get_access_token(request)
        )
        return self.sclient

    def list(self, request):
        """Retrieve list of available filter sets."""
        sclient = self.get_sieve_client(request)
        active_script, scripts = sclient.listscripts()
        result = [{"name": script, "active": False} for script in scripts]
        if active_script:
            result.insert(0, {"name": active_script, "active": True})
        return response.Response(result)

    def create(self, request):
        """Create a new filter set."""
        serializer = serializers.FilterSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sclient = self.get_sieve_client(request)
        active_script, scripts = sclient.listscripts()
        if serializer.validated_data["name"] in [active_script, *scripts]:
            raise DRFValidationError(
                {"name": _("A filter set with this name already exists")}
            )
        sclient.pushscript(
            serializer.validated_data["name"],
            "# Empty script",
            serializer.validated_data["active"],
        )
        return response.Response(serializer.validated_data, 201)

    @extend_schema(
        request=serializers.FilterSetContentSerializer,
        responses=serializers.FilterSetContentSerializer,
    )
    def update(self, request, pk):
        """Update filter set content."""
        sclient = self.get_sieve_client(request)
        sclient.getscript(pk)
        serializer = serializers.FilterSetContentSerializer(
            data=request.data, context={"sclient": sclient}
        )
        serializer.is_valid(raise_exception=True)
        try:
            sclient.pushscript(pk, serializer.validated_data["content"])
        except SieveClientError as e:
            error = str(e)
            return response.Response({"content": error}, status=400)
        return response.Response(serializer.validated_data)

    @action(methods=["post"], detail=True)
    def activate(self, request, pk):
        """Activate an existing filter set."""
        sclient = self.get_sieve_client(request)
        sclient.getscript(pk)
        try:
            sclient.activatescript(pk)
        except SieveClientError as err:
            return response.Response({"error": str(err)}, status=400)
        return response.Response()

    @action(methods=["post"], detail=False)
    def deactivate_active(self, request):
        """Deactivate the current active filterset."""
        sclient = self.get_sieve_client(request)
        try:
            sclient.activatescript("")
        except SieveClientError as err:
            return response.Response({"error": str(err)}, status=400)
        return response.Response()

    @action(methods=["get"], detail=True)
    def download(self, request, pk):
        """Download the content of an existing filter set."""
        sclient = self.get_sieve_client(request)
        script = sclient.getscript(pk)
        resp = HttpResponse(script)
        resp["Content-Type"] = "text/plain; charset=utf-8"
        resp["Content-Disposition"] = build_header(f"{pk}.txt")
        return resp

    def destroy(self, request, pk):
        """Delete an existing filter set."""
        sclient = self.get_sieve_client(request)
        sclient.getscript(pk)
        sclient.deletescript(pk)
        return response.Response(status=204)

    @extend_schema(
        description="Retrieve the list of available filter condition templates",
        responses=serializers.ConditionTemplateSerializer,
    )
    @action(methods=["get"], detail=False)
    def condition_templates(self, request):
        templates = copy.deepcopy(constants.CONDITION_TEMPLATES)
        for template in templates:
            template["operators"] = [
                {"name": operator[0], "label": operator[1], "type": operator[2]}
                for operator in template["operators"]
            ]
        serializer = serializers.ConditionTemplateSerializer(templates, many=True)
        return response.Response(serializer.data)

    @extend_schema(
        description="Retrieve the list of available filter action templates",
        responses=serializers.ActionTemplateSerializer,
    )
    @action(methods=["get"], detail=False)
    def action_templates(self, request):
        serializer = serializers.ActionTemplateSerializer(
            constants.ACTION_TEMPLATES, many=True, context={"request": request}
        )
        return response.Response(serializer.data)

    @extend_schema(
        parameters=[FILTER_SET_ID],
        responses={200: serializers.FilterSerializer(many=True)},
    )
    @action(methods=["get"], detail=True, url_path="filters")
    def get_filters(self, request, pk=None):
        """Retrieve a list of all filters associated to given filter set."""
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
            serializer = serializers.FilterSerializer.from_filters(fset.filters)
        except (SieveScriptParseError, UnsupportedSieveFilter) as err:
            # Frontend falls back to raw mode
            return response.Response({"error": str(err)}, status=422)
        return response.Response(serializer.data)

    @extend_schema(
        parameters=[FILTER_SET_ID],
        request=serializers.FilterSerializer,
        responses={201: serializers.FilterSerializer},
    )
    @get_filters.mapping.post
    def filters(self, request, pk=None):
        """Create a new filter."""
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(pk, format="fset")
        serializer = serializers.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match_type, conditions, actions = serializer.to_filter()
        fltname = serializer.validated_data["name"]
        try:
            fset.addfilter(fltname, conditions, actions, match_type)
        except (BadArgument, BadValue) as inst:
            return response.Response(str(inst), status=400)
        except FilterAlreadyExists:
            raise DRFValidationError(
                {"name": _("Filter %s already exists") % fltname}
            ) from None
        sclient.pushscript(fset.name, str(fset))
        return response.Response(serializer.validated_data, status=201)

    @extend_schema(
        description="Update an existing filter",
        parameters=[
            FILTER_SET_ID,
            OpenApiParameter(
                "filter", OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
        ],
        request=serializers.FilterSerializer,
        responses=serializers.FilterSerializer,
    )
    @action(methods=["PUT"], detail=True, url_path="filters/(?P<filter>[^/]+)")
    def update_filter(self, request, pk, filter: str):
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(pk, format="fset")
        serializer = serializers.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match_type, conditions, actions = serializer.to_filter()
        name = serializer.validated_data["name"]
        try:
            found = fset.updatefilter(filter, name, conditions, actions, match_type)
        except (BadArgument, BadValue) as inst:
            return response.Response(str(inst), status=400)
        except FilterAlreadyExists:
            raise DRFValidationError(
                {"name": _("Filter %s already exists") % name}
            ) from None
        if not found:
            return response.Response(status=404)
        sclient.pushscript(fset.name, str(fset))
        return response.Response(serializer.validated_data, status=200)

    @action(methods=["post"], detail=True, url_path="filters/(?P<filter>[^/]+)/disable")
    def disable_filter(self, request, pk, filter: str):
        """Disable an existing filter."""
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(pk, format="fset")
        if fset.getfilter(filter) is None:
            return response.Response(status=404)
        # False means the filter is already disabled
        if fset.disablefilter(filter):
            sclient.pushscript(pk, str(fset))
        return response.Response(status=204)

    @action(methods=["post"], detail=True, url_path="filters/(?P<filter>[^/]+)/enable")
    def enable_filter(self, request, pk, filter: str):
        """Enable an existing filter."""
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(pk, format="fset")
        if fset.getfilter(filter) is None:
            return response.Response(status=404)
        # False means the filter is already enabled
        if fset.enablefilter(filter):
            sclient.pushscript(pk, str(fset))
        return response.Response(status=204)

    @extend_schema(
        description="Delete an existing filter",
        parameters=[
            FILTER_SET_ID,
            OpenApiParameter(
                "filter", OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
        ],
    )
    @update_filter.mapping.delete
    def delete_filter(self, request, pk, filter: str):
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(pk, format="fset")
        if fset.removefilter(filter):
            sclient.pushscript(fset.name, str(fset))
            return response.Response(status=204)
        return response.Response(status=404)

    def move_filter(self, request, filterset: str, filter: str, direction: str):
        sclient = self.get_sieve_client(request)
        fset = sclient.getscript(filterset, format="fset")
        if fset.getfilter(filter) is None:
            return response.Response(status=404)
        # False means the filter is already at the top or bottom of the list
        if fset.movefilter(filter, direction):
            sclient.pushscript(filterset, str(fset))
        return response.Response(status=204)

    @action(methods=["post"], detail=True, url_path="filters/(?P<filter>[^/]+)/move_up")
    def move_filter_up(self, request, pk: str, filter: str):
        return self.move_filter(request, pk, filter, "up")

    @action(
        methods=["post"], detail=True, url_path="filters/(?P<filter>[^/]+)/move_down"
    )
    def move_filter_down(self, request, pk: str, filter: str):
        return self.move_filter(request, pk, filter, "down")
