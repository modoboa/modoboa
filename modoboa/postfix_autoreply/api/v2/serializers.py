"""Autoreply serializers."""

from django.utils import timezone
from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.postfix_autoreply import models


class PostfixAutoreplySettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General
    autoreplies_timeout = serializers.IntegerField(default=86400)
    default_subject = serializers.CharField(default="I'm off")
    default_content = serializers.CharField(
        default="""I'm currently off. I'll answer as soon as I come back.

Best regards,
%(name)s
"""
    )


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


class AccountARMessageSerializer(ARMessageSerializer):
    """Dedicated serializer for account operations."""

    class Meta:
        model = models.ARmessage
        fields = ("enabled", "subject", "content", "fromdate", "untildate")
