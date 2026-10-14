"""Sievefilters serializers."""

from sievelib import commands, tools
from sievelib.factory import Filter

from django.utils.translation import gettext as _

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

    def validate_name(self, value: str):
        if any(c in value for c in constants.FORBIDDEN_NAME_CHARS):
            raise serializers.ValidationError(_("Name contains forbidden characters"))
        return value


class FilterSetContentSerializer(serializers.Serializer):
    content = serializers.CharField()

    def validate_content(self, value: str):
        sclient = self.context["sclient"]
        if not sclient.msc.checkscript(value):
            error = sclient.errmsg.strip().split("\r\n")[0]
            raise serializers.ValidationError(error)
        return value


class ConditionSerializer(serializers.Serializer):
    name = serializers.CharField()
    operator = serializers.ChoiceField(choices=constants.CONDITION_OPERATORS)
    value = serializers.CharField()


class ActionSerializer(serializers.Serializer):
    name = serializers.ChoiceField(
        choices=[tpl["name"] for tpl in constants.ACTION_TEMPLATES]
    )
    args = serializers.DictField(child=serializers.CharField())


def condition_from_test(test: commands.Command) -> dict:
    """Convert a sieve test to a condition, if supported."""
    if isinstance(test, commands.SizeCommand):
        return {
            "name": "size",
            "operator": test["comparator"][1:],
            "value": test["limit"],
        }
    operator_prefix = ""
    if isinstance(test, commands.NotCommand):
        test = test["test"]
        operator_prefix = "not"
    args = test.arguments
    if (
        not isinstance(test, commands.HeaderCommand)
        or "match-type" not in args
        or not isinstance(args.get("header-names"), str)
        or not isinstance(args.get("key-list"), str)
    ):
        raise lib.UnsupportedSieveFilter(f"unsupported test {test.name}")
    operator = "{}{}".format(operator_prefix, test["match-type"][1:])
    if operator not in constants.CONDITION_OPERATORS:
        raise lib.UnsupportedSieveFilter(f"unsupported operator {operator}")
    return {
        "name": tools.unquote(test["header-names"]),
        "operator": operator,
        "value": tools.unquote(test["key-list"]),
    }


class FilterSerializer(serializers.Serializer):
    name = serializers.CharField()
    enabled = serializers.BooleanField(default=True)
    match_type = serializers.ChoiceField(choices=constants.MATCH_TYPES)
    conditions = ConditionSerializer(many=True)
    actions = ActionSerializer(many=True)

    def validate_name(self, value: str):
        if any(c in value for c in constants.FORBIDDEN_NAME_CHARS):
            raise serializers.ValidationError(_("Name contains forbidden characters"))
        if value == "autoreply":
            raise serializers.ValidationError(_("This name is reserved"))
        return value

    @staticmethod
    def from_filters(filters: list[Filter]) -> "FilterSerializer":
        """Convert filters to serializer data.

        Raise UnsupportedSieveFilter if a filter can't be represented.
        """
        result = []
        for fobj in filters:
            if fobj["name"] == "autoreply":
                continue
            test = (
                fobj["content"].children[0] if not fobj["enabled"] else fobj["content"]
            )
            test_node = test.arguments.get("test")
            if test_node is None:
                raise lib.UnsupportedSieveFilter(f"unsupported command {test.name}")
            item = {
                "name": fobj["name"],
                "enabled": fobj["enabled"],
                "match_type": test_node.name,
                "conditions": [],
                "actions": [],
            }
            if isinstance(test_node, commands.TrueCommand):
                item["match_type"] = "all"
                item["conditions"] += [
                    {"name": "Subject", "operator": "contains", "value": ""}
                ]
            else:
                if "tests" in test_node.arguments:
                    subtests = test_node["tests"]
                else:
                    # A single test is equivalent to anyof (test)
                    item["match_type"] = constants.MATCH_TYPE_ANYOF
                    subtests = [test_node]
                item["conditions"] = [condition_from_test(t) for t in subtests]
            for c in test.children:
                action = {"name": c.name, "args": {}}
                tpl = lib.find_action_template(c.name)
                for argtpl in tpl.get("args", []):
                    if argtpl["name"] not in c:
                        continue
                    value = tools.unquote(c[argtpl["name"]])
                    action["args"][argtpl["name"]] = value
                item["actions"] += [action]
            result.append(item)
        return FilterSerializer(result, many=True)

    def to_filter(self) -> tuple[str, list, list]:
        """Convert serializer data to filter representation."""
        conditions: list[tuple] = []
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
