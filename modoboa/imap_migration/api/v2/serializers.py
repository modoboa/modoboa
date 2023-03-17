"""APIv2 serializers."""

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
    new_domain = serializers.CharField()

    def validate(self, data):
        if data["initialdomain"] != data["new_domain"]:
            if not Domain.objects.filter(name=data["initialdomain"]):
                raise ValidationError({"new_domain": [
                    _("You must create the local domain first.")]
                    })
        return data

