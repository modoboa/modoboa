"""RelayDomain serializers."""

import json

from django.utils.translation import ugettext as _

from rest_framework import serializers

from modoboa.admin import models as admin_models
from modoboa.transport import backends as tr_backends, models as tr_models


class TransportSerializer(serializers.ModelSerializer):
    """Transport serializer."""

    class Meta:
        model = tr_models.Transport
        fields = ("pk", "service", "_settings")

    def validate(self, data):
        """Check fields based on backend."""
        self.backend = tr_backends.manager.get_backend(data["service"])
        if not self.backend:
            raise serializers.ValidationError({
                "service": _("Unsupported service")
            })
        data["_settings"] = json.loads(data["_settings"])
        errors = self.backend.clean_fields(data["_settings"])
        if errors:
            raise serializers.ValidationError({
                "_settings": ",".join(
                    ["{}: {}".format(error[0], error[1]) for error in errors])
            })
        return data


class RelayDomainSerializer(serializers.ModelSerializer):
    """RelayDomain serializer class."""

    transport = TransportSerializer()

    class Meta:
        model = admin_models.Domain
        fields = (
            "pk", "name", "enabled", "transport", "enable_dkim",
            "dkim_key_selector", "dkim_public_key"
        )
        read_only_fields = ("pk", "dkim_public_key", )

    def create(self, validated_data):
        """Use backend to serialize data."""
        transport = tr_models.Transport(**validated_data.pop("transport"))
        transport.pattern = validated_data["name"]
        transport.save()
        domain = admin_models.Domain(**validated_data)
        domain.type = "relaydomain"
        domain.transport = transport
        domain.save(creator=self.context["request"].user)
        return domain

    def update(self, instance, validated_data):
        """Use backend to serialize data."""
        transport_data = validated_data.pop("transport")
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        for key, value in transport_data.items():
            setattr(instance.transport, key, value)
        instance.transport.pattern = instance.name
        instance.transport.save()
        return instance
