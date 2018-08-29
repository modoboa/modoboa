"""Core serializers."""

from django.utils.translation import ugettext_lazy, ugettext as _

from django.contrib.auth import password_validation

from rest_framework import serializers

from . import constants


class CoreGlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General settings
    authentication_type = serializers.ChoiceField(
        choices=[("local", ugettext_lazy("Local")),
                 ("ldap", "LDAP")],
        default="local"
    )
    password_scheme = serializers.ChoiceField(
        choices=[("sha512crypt", "sha512crypt"),
                 ("sha256crypt", "sha256crypt"),
                 ("blfcrypt", "bcrypt"),
                 ("md5crypt", ugettext_lazy("md5crypt (weak)")),
                 ("sha256", ugettext_lazy("sha256 (weak)")),
                 ("md5", ugettext_lazy("md5 (weak)")),
                 ("crypt", ugettext_lazy("crypt (weak)")),
                 ("plain", ugettext_lazy("plain (weak)"))],
        default="sha512crypt"
    )
    rounds_number = serializers.IntegerField(default=70000)
    default_password = serializers.CharField(default="password")
    random_password_length = serializers.IntegerField(min_value=8, default=8)

    # LDAP settings
    ldap_server_address = serializers.CharField(default="localhost")
    ldap_server_port = serializers.IntegerField(default=389)
    ldap_secured = serializers.ChoiceField(
        choices=constants.LDAP_SECURE_MODES,
        default="none"
    )
    ldap_auth_method = serializers.ChoiceField(
        choices=constants.LDAP_AUTH_METHODS,
        default="searchbind",
    )
    ldap_bind_dn = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_bind_password = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_search_base = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_search_filter = serializers.CharField(
        default="(mail=%(user)s)", required=False,
        allow_blank=True)
    ldap_user_dn_template = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_password_attribute = serializers.CharField(default="userPassword")
    ldap_is_active_directory = serializers.BooleanField(default=False)
    ldap_admin_groups = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_group_type = serializers.ChoiceField(
        default="posixgroup",
        choices=constants.LDAP_GROUP_TYPES
    )
    ldap_groups_search_base = serializers.CharField(
        default="", required=False, allow_blank=True)

    def validate_ldap_user_dn_template(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError):
            raise serializers.ValidationError(_("Invalid syntax"))
        return value

    def validate_rounds_number(self, value):
        if value < 1000 or value > 999999999:
            raise serializers.ValidationError(_("Invalid rounds number"))
        return value

    def validate_default_password(self, value):
        """Check password complexity."""
        password_validation.validate_password(value)
        return value

    def validate(self, data):
        """Custom validation method

        Depending on 'ldap_auth_method' value, we check for different
        required parameters.
        """
        if data["authentication_type"] != "ldap":
            return data
        if data["ldap_auth_method"] == "searchbind":
            required_fields = ["ldap_search_base", "ldap_search_filter"]
        else:
            required_fields = ["ldap_user_dn_template"]
        errors = {}
        for f in required_fields:
            if data.get(f, u"") == u"":
                errors[f] = _("This field is required")
        if len(errors):
            raise serializers.ValidationError(errors)
        return data
