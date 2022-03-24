"""Transport related serializers."""

from rest_framework import serializers

from ... import backends
from ... import models


class TransportBackendSettingSerializer(serializers.Serializer):
    """Serializer for transport backend setting."""

    name = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField(default="str")
    required = serializers.BooleanField(default=True)
    default = serializers.CharField(default=None)


class TransportBackendSerializer(serializers.Serializer):
    """Serializer for transport backend."""

    name = serializers.CharField()
    settings = TransportBackendSettingSerializer(many=True)


class TransportSerializer(serializers.ModelSerializer):
    """Serializer for Transport model."""

    settings = serializers.DictField(source="_settings")

    class Meta:
        fields = ("service", "settings")
        model = models.Transport

    def validate(self, data):
        self.backend = backends.manager.get_backend(data["service"])
        errors = {}
        for field, error in self.backend.clean_fields(data["_settings"]):
            errors[field] = error
        if errors:
            raise serializers.ValidationError(errors)
        return data
