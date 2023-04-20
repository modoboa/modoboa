"""Parameters serializers."""

from rest_framework import serializers


class ApplicationSerializer(serializers.Serializer):
    """Application serializer."""

    name = serializers.CharField()
    label = serializers.CharField()
    is_extension = serializers.BooleanField()


class ParameterChoiceSerializer(serializers.Serializer):
    """Parameter choice serializer."""

    text = serializers.CharField()
    value = serializers.CharField()


class ParameterSerializer(serializers.Serializer):
    """Parameter serializer."""

    name = serializers.CharField()
    label = serializers.CharField()
    help_text = serializers.CharField()
    display = serializers.CharField()
    widget = serializers.CharField()
    choices = ParameterChoiceSerializer(many=True)


class StructureSerializer(serializers.Serializer):
    """Structure serializer."""

    name = serializers.CharField()
    display = serializers.CharField(help_text="Display rule")
    parameters = ParameterSerializer(many=True)


class AppParametersSerializer(serializers.Serializer):
    """Serializer for application parameters."""

    label = serializers.CharField()
    params = serializers.DictField()
