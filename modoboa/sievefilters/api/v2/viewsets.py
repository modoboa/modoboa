"""Sievefilters viewsets."""

import copy

from rest_framework import response, viewsets
from rest_framework.decorators import action

from modoboa.lib.connections import ConnectionError
from modoboa.sievefilters import constants
from modoboa.sievefilters.lib import SieveClient, SieveClientError
from modoboa.sievefilters.api.v2 import serializers


class FilterSetViewSet(viewsets.ViewSet):

    serializer_class = serializers.FilterSetSerializer

    def get_sieve_client(self, request):
        # try:
        return SieveClient(user=request.user.username, password=str(request.auth))
        # except ConnectionError as e:
        # raise

    def list(self, request):
        sclient = self.get_sieve_client(request)
        active_script, scripts = sclient.listscripts()
        scripts = [
            {"name": script, "active": active_script == script} for script in scripts
        ]
        return response.Response(scripts)

    def create(self, request):
        serializer = serializers.FilterSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sclient = self.get_sieve_client(request)
        sclient.pushscript(
            serializer.validated_data["name"],
            "# Empty script",
            serializer.validated_data["active"],
        )
        return response.Response(serializer.validated_data, 201)

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

    @action(methods=["get"], detail=False)
    def action_templates(self, request):
        serializer = serializers.ActionTemplateSerializer(
            constants.ACTION_TEMPLATES, many=True
        )
        return response.Response(serializer.data)

    @action(methods=["get", "post"], detail=True)
    def filters(self, request, pk=None):
        sclient = self.get_sieve_client(request)
        try:
            fset = sclient.getscript(pk, format="gui")
        except SieveClientError:
            return response.Response(status=404)
        if request.method == "GET":
            serializer = serializers.FilterSerializer.from_filters(fset.filters)
            return response.Response(serializer.data)
        serializer = serializers.FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conditions, actions = serializer.to_filter()
        match_type = serializer.validated_data["match_type"]
        if match_type == "all":
            match_type = "anyof"
            conditions = [("true",)]
        fltname = serializer.validated_data["name"].encode("utf-8")
        try:
            fset.addfilter(fltname, conditions, actions, match_type)
        except (BadArgument, BadValue) as inst:
            return response.Response(str(inst), status=400)
        sclient.pushscript(fset.name, "{}".format(fset))
        return response.Response(serializer.validated_data, status=201)

    # @action(methods=["delete"], detail=True, url_path="filters/{filter}")
    # def delete_filter(self, request, pk=None):
    #     sclient = self.get_sieve_client(request)
    #     return response.Response(status=204)
