"""Modoboa rspamd serializer for api v2."""

import os

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


def validate_file_path(value: str) -> None:
    if value:
        if os.path.isfile(value):
            if not os.access(value, os.W_OK):
                # File exists and is writable by modoboa
                raise serializers.ValidationError(_("Provided path is not writable."))
        elif not os.path.isdir(os.path.dirname(value)):
            raise serializers.ValidationError(
                _("Please create the parent directory for the files")
            )
        elif not os.access(os.path.dirname(value), os.W_OK):
            # File doesn't exist and modoboa won't be able to create it...
            raise serializers.ValidationError(_("Unable to write to the directory."))


class RspamdSettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # dkim_settings_sep
    key_map_path = serializers.CharField(
        default="/var/lib/dkim/keys.path.map", allow_blank=True
    )
    selector_map_path = serializers.CharField(
        default="/var/lib/dkim/selectors.path.map", allow_blank=True
    )

    # miscellaneous_sep
    rspamd_dashboard_location = serializers.CharField(
        default="/rspamd", allow_blank=True
    )

    def validate_key_map_path(self, value):
        validate_file_path(value)
        return value

    def validate_selector_map_path(self, value):
        validate_file_path(value)
        return value
