"""Core API serializers."""

import logging

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.core import models
from modoboa.parameters import tools as param_tools

logger = logging.getLogger("modoboa.auth")


class AccountPasswordSerializer(serializers.ModelSerializer):
    """A serializer used to change a user password."""

    new_password = serializers.CharField()

    class Meta:
        model = models.User
        fields = (
            "password",
            "new_password",
        )

    def validate_password(self, value):
        """Check password."""
        authentication_type = param_tools.get_global_parameter("authentication_type")
        if authentication_type != "ldap":
            check = self.instance.check_password(value)
        else:
            from django_auth_ldap.backend import LDAPBackend

            check = LDAPBackend().authenticate(
                self.context["request"], self.instance.username, value
            )
        if not check:
            raise serializers.ValidationError("Password not correct")
        return value

    def validate_new_password(self, value):
        """Check new password."""
        try:
            password_validation.validate_password(value, self.instance)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from None
        return value

    def update(self, instance, validated_data):
        """Set new password."""
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


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
