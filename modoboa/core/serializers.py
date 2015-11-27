"""Modoboa core serializers."""

from django.core.exceptions import ValidationError

from rest_framework import serializers
from passwords import validators

from . import models


class UserPasswordSerializer(serializers.ModelSerializer):

    """A serializer used to change a user password."""

    new_password = serializers.CharField()

    class Meta:
        model = models.User
        fields = (
            "password", "new_password", )

    def validate_password(self, value):
        """Check password."""
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Password not correct")
        return value

    def validate_new_password(self, value):
        """Check new password."""
        try:
            validators.validate_length(value)
            validators.complexity(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value

    def update(self, instance, validated_data):
        """Set new password."""
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance
