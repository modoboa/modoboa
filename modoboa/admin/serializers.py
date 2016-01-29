"""Admin serializers."""

from rest_framework import serializers

from . import models


class DomainSerializer(serializers.ModelSerializer):

    """Base Domain serializer."""

    class Meta:
        model = models.Domain
        fields = ("pk", "name", "quota", "enabled", "type", )
