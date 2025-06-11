"""Autoreply serializers."""

from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.autoreply import models


class AutoreplySettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General
    tracking_period = serializers.IntegerField(default=7)
    default_subject = serializers.CharField(default="I'm off")
    default_content = serializers.CharField(
        default="""I'm currently off. I'll answer as soon as I come back.

Best regards,
%(name)s
"""
    )

    def validate_tracking_period(self, value):
        if value < 1:
            raise serializers.ValidationError(_("Value can't be less than 1 day"))
        return value


class ARMessageSerializer(serializers.ModelSerializer):
    """A serializer for ARmessage."""

    class Meta:
        model = models.ARmessage
        fields = "__all__"

    def validate(self, data):
        """Check dates."""
        if not data.get("fromdate"):
            data["fromdate"] = timezone.now()
        if not data["enabled"]:
            return data
        untildate = data.get("untildate")
        if untildate is not None:
            if untildate < timezone.now():
                raise serializers.ValidationError({"untildate": _("This date is over")})
            elif untildate < data["fromdate"]:
                raise serializers.ValidationError(
                    {"untildate": _("Must be greater than start date")}
                )
        return data

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.manage_sieve_rule(self.context["request"])
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.manage_sieve_rule(self.context["request"])
        return instance


class AccountARMessageSerializer(ARMessageSerializer):
    """Dedicated serializer for account operations."""

    class Meta:
        model = models.ARmessage
        fields = ("enabled", "subject", "content", "fromdate", "untildate")
