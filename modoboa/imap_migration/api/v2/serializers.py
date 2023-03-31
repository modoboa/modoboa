"""API v2 serializers."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from modoboa.admin.models.domain import Domain


class IMAPMigrationSettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General
    enabled_imapmigration = serializers.BooleanField(default=True)

    # OfflineIMAP settings
    max_sync_accounts = serializers.IntegerField(default=1)

    # OfflineIMAP Filter settings
    create_folders = serializers.BooleanField(default=True)
    folder_filter_exclude = serializers.CharField(required=False,
                                                  allow_blank=True,
                                                  default="")
    folder_filter_include = serializers.CharField(required=False,
                                                  allow_blank=True,
                                                  default="")


class CheckProviderSerializer(serializers.Serializer):
    """A serializer for checking connection to IMAP server."""

    address = serializers.CharField()
    port = serializers.IntegerField(min_value=0, max_value=65535)
    secured = serializers.BooleanField()


class CheckAssociatedDomainSerializer(serializers.Serializer):
    """A serializer for checking associated domains."""

    initialdomain = serializers.CharField()
    new_domain = serializers.PrimaryKeyRelatedField(
        read_only=True, required=False)

    def validate_new_domain(self, value):
        domain_ids = (
            Domain.objects.get_for_admin(self.context["request"].user)
            .values_list("id", flat=True)
        )
        if value not in domain_ids:
            raise serializers.ValidationError(_("Access denied"))
        return value
