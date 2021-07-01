"""App. related serializers."""

from django.utils.translation import ugettext as _

from rest_framework import serializers

from ... import models


PERIODS = [
    ("day", "Day"),
    ("week", "Week"),
    ("month", "Month"),
    ("year", "Year"),
    ("custom", "Custom")
]


class StatisticsInputSerializer(serializers.Serializer):
    """Serializer used to filter statistics."""

    gset = serializers.CharField()
    period = serializers.ChoiceField(choices=PERIODS)
    graphic = serializers.CharField(required=False)
    searchquery = serializers.CharField(required=False)
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)

    def validate(self, data):
        condition = (
            data["period"] == "custom" and
            (not data.get("start") or not data.get("end"))
        )
        if condition:
            raise serializers.ValidationError(
                _("You must provide start and end dates when period is custom")
            )
        return data


class GraphPointSerializer(serializers.Serializer):
    """A serializer to represent a point in a curve."""

    x = serializers.FloatField()
    y = serializers.FloatField()


class GraphCurveSerializer(serializers.Serializer):
    """A serializer to represent a curve in a graph."""

    name = serializers.CharField()
    backgroundColor = serializers.CharField()
    data = GraphPointSerializer(many=True)


class GraphSerializer(serializers.Serializer):
    """A serializer to represent a graph."""

    title = serializers.CharField()
    series = GraphCurveSerializer(many=True)


class StatisticsSerializer(serializers.Serializer):
    """Serializer to return statistics."""

    graphs = GraphSerializer(many=True)


class MaillogSerializer(serializers.ModelSerializer):
    """Serializer for Maillog model."""

    class Meta:
        fields = (
            "id", "queue_id", "date", "sender", "rcpt", "original_rcpt",
            "size", "status"
        )
        model = models.Maillog
