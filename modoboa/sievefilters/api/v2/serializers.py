"""Sievefilters serializers."""

from typing import List, Tuple

from sievelib import commands
from sievelib.factory import Filter

from rest_framework import serializers

from modoboa.sievefilters import constants, lib
from modoboa.sievefilters.api.v2 import vloaders


class SievefiltersSettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # ManageSieve settings

    server = serializers.CharField(default="127.0.0.1")
    port = serializers.IntegerField(default=4190)
    starttls = serializers.BooleanField(default=False)

    # Imap Settings
    imap_server = serializers.CharField(default="127.0.0.1")
    imap_secured = serializers.BooleanField(default=False)
    imap_port = serializers.IntegerField(default=143)


class FilterSetSerializer(serializers.Serializer):
    name = serializers.CharField()
    active = serializers.BooleanField(default=False)


class FilterSetContentSerializer(serializers.Serializer):
    content = serializers.CharField()

    def validate_content(self, value: str):
        sclient = self.context["sclient"]
        if not sclient.msc.checkscript(value):
            error = sclient.msc.errmsg.decode().strip().split("\r\n")[0]
            raise serializers.ValidationError(error)
        return value


class ConditionSerializer(serializers.Serializer):
    name = serializers.CharField()
    operator = serializers.CharField()
    value = serializers.CharField()


class ActionSerializer(serializers.Serializer):
    name = serializers.CharField()
    args = serializers.DictField(child=serializers.CharField())


class FilterSerializer(serializers.Serializer):
    name = serializers.CharField()
    enabled = serializers.BooleanField(default=True)
    match_type = serializers.ChoiceField(choices=constants.MATCH_TYPES)
    conditions = ConditionSerializer(many=True)
    actions = ActionSerializer(many=True)

    @staticmethod
    def from_filters(filters: List[Filter]) -> "FilterSerializer":
        result = []
        for fobj in filters:
            test = (
                fobj["content"].children[0] if not fobj["enabled"] else fobj["content"]
            )
            item = {
                "name": fobj["name"],
                "enabled": fobj["enabled"],
                "match_type": test["test"].name,
                "conditions": [],
                "actions": [],
            }
            if isinstance(test["test"], commands.TrueCommand):
                item["match_type"] = "all"
                item["conditions"] += [
                    {"name": "Subject", "operator": "contains", "value": ""}
                ]
            else:
                for t in test["test"]["tests"]:
                    if isinstance(t, commands.SizeCommand):
                        item["conditions"] += [
                            {
                                "name": "size",
                                "operator": t["comparator"][1:],
                                "value": t["limit"],
                            }
                        ]
                    else:
                        operator_prefix = ""
                        if isinstance(t, commands.NotCommand):
                            t = t["test"]
                            operator_prefix = "not"
                        item["conditions"] += [
                            {
                                "name": t["header-names"].strip('"'),
                                "operator": "{}{}".format(
                                    operator_prefix, t["match-type"][1:]
                                ),
                                "value": t["key-list"].strip('"'),
                            }
                        ]
            for c in test.children:
                action = {"name": c.name, "args": {}}
                tpl = lib.find_action_template(c.name)
                for argtpl in tpl.get("args", []):
                    if argtpl["name"] not in c:
                        continue
                    value = c[argtpl["name"]].strip('"')
                    action["args"][argtpl["name"]] = value
                item["actions"] += [action]
            result.append(item)
        return FilterSerializer(result, many=True)

    def to_filter(self) -> Tuple[str, List, List]:
        """Convert serializer data to filter representation."""
        conditions: List[Tuple] = []
        actions = []
        match_type = self.validated_data["match_type"]
        if match_type == "all":
            match_type = "anyof"
            conditions = [("true",)]
        else:
            for condition in self.validated_data["conditions"]:
                conditions.append(
                    (condition["name"], f":{condition['operator']}", condition["value"])
                )
        for input_action in self.validated_data["actions"]:
            action = [input_action["name"]]
            tpl = lib.find_action_template(input_action["name"])
            if "args_order" in tpl:
                for name in tpl["args_order"]:
                    if name in input_action["args"]:
                        action.append(input_action["args"][name])
            else:
                action += [arg for arg in input_action["args"].values()]
            actions.append(action)
        return (match_type, conditions, actions)


class OperatorSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField()


class ConditionTemplateSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    operators = OperatorSerializer(many=True)


class ActionArgumentSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    label = serializers.CharField(required=False)
    value = serializers.CharField(required=False)
    choices = serializers.SerializerMethodField(required=False)

    def get_choices(self, obj):
        if "vloader" not in obj:
            return None
        loader = getattr(vloaders, obj["vloader"])
        return loader(self.context["request"])


class ActionTemplateSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    args = ActionArgumentSerializer(many=True, required=False)
    args_order = serializers.ListField(child=serializers.CharField(), required=False)
