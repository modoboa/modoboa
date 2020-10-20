"""Core API serializers."""

from django.utils.translation import ugettext as _
from rest_framework import serializers


class CheckTFASetupSerializer(serializers.Serializer):
    """Serializer used to finalize 2FA setup."""

    pin_code = serializers.CharField()

    def validate_pin_code(self, value):
        device = self.context["user"].totpdevice_set.first()
        if not device.verify_token(value):
            raise serializers.ValidationError(_("Invalid PIN code"))
        return value

    def validate(self, data):
        user = self.context["user"]
        if user.tfa_enabled or user.staticdevice_set.exists():
            raise serializers.ValidationError(_("2FA is already enabled"))
        return data
