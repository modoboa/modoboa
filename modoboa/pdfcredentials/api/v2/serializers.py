"""Limits serializers for API v2."""

import os

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from django.contrib.sites import models as sites_models

from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, APIException

from modoboa.core.models import User
from modoboa.parameters import tools as param_tools

from ...lib import decrypt_file, get_creds_filename
from ...constants import CONNECTION_SECURITY_MODES


class PDFCredentialsSettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General
    enabled_pdfcredentials = serializers.BooleanField(default=True)

    # Document storage
    storage_dir = serializers.CharField(default="/var/lib/modoboa/pdf_credentials")

    # Security options
    delete_first_dl = serializers.BooleanField(default=True)
    generate_at_creation = serializers.BooleanField(default=True)

    # Customization options
    title = serializers.CharField(default=_("Personal account information"))
    webpanel_url = serializers.URLField()
    custom_message = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    include_connection_settings = serializers.BooleanField(default=False)
    smtp_server_address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    smtp_server_port = serializers.IntegerField(default=587)
    smtp_connection_security = serializers.ChoiceField(
        choices=CONNECTION_SECURITY_MODES, default="starttls"
    )
    imap_server_address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    imap_server_port = serializers.IntegerField(default=143)
    imap_connection_security = serializers.ChoiceField(
        choices=CONNECTION_SECURITY_MODES, default="starttls"
    )

    @cached_property
    def hostname(self):
        """Return local hostname."""
        return sites_models.Site.objects.get_current().domain

    def __init__(self, *args, **kwargs):
        """Set initial values."""
        super().__init__(*args, **kwargs)
        if not self.fields["webpanel_url"].default:
            url = f"https://{self.hostname}{settings.LOGIN_URL}"
            self.fields["webpanel_url"].default = url
        if not self.fields["smtp_server_address"].default:
            self.fields["smtp_server_address"].default = self.hostname
        if not self.fields["imap_server_address"].default:
            self.fields["imap_server_address"].default = self.hostname

    def validate(self, data):
        """Check that directory exists."""
        enabled_pdfcredentials = data.get("enabled_pdfcredentials", None)
        condition = enabled_pdfcredentials or (
            enabled_pdfcredentials is None
            and param_tools.get_global_parameter("enabled_pdfcredentials")
        )
        errors = {}
        if condition:
            storage_dir = data.get("storage_dir", None)
            if storage_dir is not None:
                if not os.path.isdir(storage_dir):
                    errors["storage_dir"] = _("Directory not found.")
                elif not os.access(storage_dir, os.W_OK):
                    errors["storage_dir"] = _("Directory is not writable")
            include_connection_settings = data.get("include_connection_settings")
            if include_connection_settings:
                for field in ["smtp_server_address", "imap_server_address"]:
                    if not data.get(field):
                        errors[field] = _("This field is required.")
        if errors:
            raise serializers.ValidationError(errors)
        return data


class GetAccountCredentialsSerializer(serializers.Serializer):
    """A serializer for get account credential view."""

    account_id = serializers.IntegerField()

    def validate(self, data):
        request = self.context["request"]
        account = User.objects.get(pk=data["account_id"])
        if not request.user.can_access(account):
            raise PermissionDenied()
        self.context["account"] = account
        return data

    def save(self):
        fname = get_creds_filename(self.context["account"])
        if not os.path.exists(fname):
            raise APIException(
                _("No document available for this user"), status.HTTP_400_BAD_REQUEST
            )
        self.context["content"] = decrypt_file(fname)
        if param_tools.get_global_parameter("delete_first_dl"):
            os.remove(fname)
        self.context["fname"] = os.path.basename(fname)
