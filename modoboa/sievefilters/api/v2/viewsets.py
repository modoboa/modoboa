"""Sievefilters viewsets."""

import copy
from typing import Optional

from sievelib.commands import BadArgument, BadValue
from sievelib.factory import FilterAlreadyExists

from django.http import HttpResponse

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import response, viewsets
from rest_framework.decorators import action

from modoboa.lib.connections import ConnectionError
from modoboa.sievefilters import constants
from modoboa.sievefilters.lib import SieveClient, SieveClientError
from modoboa.sievefilters.rfc6266 import build_header
from modoboa.sievefilters.api.v2 import serializers


class FilterSetViewSet(viewsets.ViewSet):

    serializer_class = serializers.FilterSetSerializer

    def get_sieve_client(self, request):
        # try:
        return SieveClient(user=request.user.username, password=str(request.auth))
        # except ConnectionError as e:
        # raise

    def list(self, request):
        """Retrieve list of available filter sets."""
        sclient = self.get_sieve_client(request)
        active_script, scripts = sclient.listscripts()
        scripts = [
            {"name": active_script, "active": True},
        ] + [{"name": script, "active": False} for script in scripts]
        return response.Response(scripts)

    def create(self, request):
        """Create a new filter set."""
        serializer = serializers.FilterSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sclient = self.get_sieve_client(request)
        sclient.pushscript(
            serializer.validated_data["name"],
            "# Empty script",
            serializer.validated_data["active"],
        )
        return response.Response(serializer.validated_data, 201)

    @action(methods=["post"], detail=True)
    def activate(self, request, pk):
        """Activate an existing filter set."""
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        try:
            sclient.activatescript(pk)
        except SieveClientError as err:
            return response.Response({"error": str(err)}, status=400)
        return response.Response()

    @action(methods=["get"], detail=True)
    def download(self, request, pk):
        """Download the content of an existing filter set."""
        sclient = self.get_sieve_client(request)
        try:
            script = sclient.getscript(pk)
        except SieveClientError:
            return response.Response(status=404)
        resp = HttpResponse(script)
        resp["Content-Type"] = "text/plain; charset=utf-8"
        resp["Content-Length"] = len(script)
        resp["Content-Disposition"] = build_header(f"{pk}.txt")
        return resp

    def destroy(self, request, pk):
        """Delete an existing filter set."""
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
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
            constants.ACTION_TEMPLATES, many=True
        )
        return response.Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter("id", OpenApiTypes.STR),
        ],
        request=serializers.FilterSerializer,
        responses={201: serializers.FilterSerializer},
    )
    @action(methods=["get", "post"], detail=True)
    def filters(self, request, pk=None):
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        if request.method == "GET":
            serializer = serializers.FilterSerializer.from_filters(fset.filters)
            return response.Response(serializer.data)
        serializer = serializers.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match_type, conditions, actions = serializer.to_filter()
        fltname = serializer.validated_data["name"]
        try:
            fset.addfilter(fltname, conditions, actions, match_type)
        except (BadArgument, BadValue) as inst:
            return response.Response(str(inst), status=400)
        except FilterAlreadyExists:
            return response.Response(
                {"error": f"Filter {fset.name} already exists"}, status=409
            )
        sclient.pushscript(fset.name, str(fset))
        return response.Response(serializer.validated_data, status=201)

    @extend_schema(
        description="Update an existing filter",
        parameters=[
            OpenApiParameter("id", OpenApiTypes.STR, location=OpenApiParameter.PATH),
            OpenApiParameter(
                "filter", OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
        ],
        request=serializers.FilterSerializer,
        responses=serializers.FilterSerializer,
    )
    @action(methods=["PUT"], detail=True, url_path="filters/(?P<filter>[^/.]+)")
    def update_filter(self, request, pk, filter: str):
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        serializer = serializers.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match_type, conditions, actions = serializer.to_filter()
        name = serializer.validated_data["name"]
        try:
            fset.updatefilter(filter, name, conditions, actions, match_type)
        except (BadArgument, BadValue) as inst:
            return response.Response(str(inst), status=400)
        sclient.pushscript(fset.name, str(fset))
        return response.Response(serializer.validated_data, status=200)

    @action(
        methods=["post"], detail=True, url_path="filters/(?P<filter>[^/.]+)/disable"
    )
    def disable_filter(self, request, pk, filter: str):
        """Disable an existing filter."""
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        if not fset.disablefilter(filter):
            return response.Response(status=404)
        sclient.pushscript(pk, str(fset))
        return response.Response(status=204)

    @action(methods=["post"], detail=True, url_path="filters/(?P<filter>[^/.]+)/enable")
    def enable_filter(self, request, pk, filter: str):
        """Enable an existing filter."""
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        if not fset.enablefilter(filter):
            return response.Response(status=404)
        sclient.pushscript(pk, str(fset))
        return response.Response(status=204)

    @extend_schema(
        description="Delete an existing filter",
        parameters=[
            OpenApiParameter("id", OpenApiTypes.STR, location=OpenApiParameter.PATH),
            OpenApiParameter(
                "filter", OpenApiTypes.STR, location=OpenApiParameter.PATH
            ),
        ],
    )
    @update_filter.mapping.delete
    def delete_filter(self, request, pk, filter: str):
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="fset")
        except SieveClientError:
            return response.Response(status=404)
        if fset.removefilter(filter):
            sclient.pushscript(fset.name, str(fset))
            return response.Response(status=204)
        return response.Response(status=404)
