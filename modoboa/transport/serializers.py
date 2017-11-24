"""Transport serializers."""

from django.utils.translation import ugettext as _

from rest_framework import serializers

from . import backends
from . import models


class TransportSerializer(serializers.ModelSerializer):
    """Transport serializer class."""

    class Meta:
        model = models.Transport
        fields = ("pk", "pattern", "service", "enabled", "_settings")

    def validate(self, data):
        """Check fields based on backend."""
        self.backend = backends.manager.get_backend(data["service"])
        if not self.backend:
            raise serializers.ValidationError({
                "service": _("Unsupported service")
            })
        errors = self.backend.clean_fields(data)
        if errors:
            raise serializers.ValidationError({
                "_settings": ",".join(
                    ["{}: {}".format(error[0], error[1]) for error in errors])
            })
        return data

    def create(self, validated_data):
        """Use backend to serialize data."""
        transport = models.Transport(**validated_data)
        self.backend.serialize(transport)
        transport.save(creator=self.context["request"].user)
        return transport

    def update(self, instance, validated_data):
        """Use backend to serialize data."""
        for key, value in validated_data.items():
            setattr(instance, key, value)
        self.backend.serialize(instance)
        instance.save()
        return instance
