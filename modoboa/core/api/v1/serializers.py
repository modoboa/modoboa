"""Core API serializers."""

import logging

from django.utils.html import escape
from django.utils.translation import gettext as _

from rest_framework import serializers

logger = logging.getLogger("modoboa.auth")


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
        if user.totp_enabled:
            raise serializers.ValidationError(_("2FA is already enabled"))
        return data


class CheckPasswordTFASerializer(serializers.Serializer):
    """Serializer used to check user password when modifying TFA."""

    password = serializers.CharField()

    def validate_password(self, value):
        user = self.context["user"]
        if not user.check_password(value):
            logger.warning(
                _("Failed TFA settings editing attempt from '%s' as user '%s'"),
                self.context["remote_addr"],
                escape(user.username),
            )
            raise serializers.ValidationError(_("Invalid password"))
        return value
