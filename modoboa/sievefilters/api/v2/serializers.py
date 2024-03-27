"""Sievefilters serializers."""

from sievelib import commands

from rest_framework import serializers

from modoboa.sievefilters import constants, lib


class FilterSetSerializer(serializers.Serializer):

    name = serializers.CharField()
    active = serializers.BooleanField(default=False)


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
    def from_filters(filters) -> "FilterSerializer":
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
            for t in test["test"]["tests"]:
                print(t)
                if isinstance(t, commands.TrueCommand):
                    item["match_type"] = "all"
                    item["conditions"] += [
                        {name: "Subject", "operator": "contains", value: ""}
                    ]
                    break
                elif isinstance(t, commands.SizeCommand):
                    item["conditions"] += [
                        {
                            name: "size",
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
                    value = c[argtpl["name"]]
                    if argtpl["type"] == "boolean":
                        value = True if value else False
                    else:
                        value = value.strip('"')
                    action["args"][argtpl["name"]] = value
                item["actions"] += [action]
            result.append(item)
        return FilterSerializer(result, many=True)

    def to_filter(self):
        """Convert serializer data to filter."""
        conditions = []
        actions = []
        for condition in self.validated_data["conditions"]:
            conditions.append(
                [condition["name"], f":{condition['operator']}", condition["value"]]
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
        return (conditions, actions)


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


class ActionTemplateSerializer(serializers.Serializer):

    name = serializers.CharField()
    label = serializers.CharField()
    args = ActionArgumentSerializer(many=True, required=False)
    args_order = serializers.ListField(child=serializers.CharField(), required=False)
