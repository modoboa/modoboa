"""Core API v2 serializers."""

import django_otp

from django.conf import settings

from django.contrib.auth import authenticate, password_validation


from django.utils import formats
from django.utils.translation import gettext_lazy, gettext as _

from rest_framework import serializers

from modoboa.core import (
    constants,
    models,
    sms_backends,
    app_settings,
)
from modoboa.lib import fields as lib_fields
from modoboa.parameters import tools as param_tools


class CoreGlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General settings
    authentication_type = serializers.ChoiceField(
        choices=[("local", gettext_lazy("Local")), ("ldap", "LDAP")], default="local"
    )
    password_scheme = serializers.ChoiceField(
        choices=[("sha512crypt", "sha512crypt")], default="sha512crypt", required=False
    )
    rounds_number = serializers.IntegerField(default=70000)
    update_scheme = serializers.BooleanField(default=True)
    default_password = serializers.CharField(default="ChangeMe1!")
    random_password_length = serializers.IntegerField(min_value=8, default=8)
    allow_special_characters = serializers.BooleanField(default=False)
    update_password_url = serializers.URLField(
        required=False, allow_blank=True, allow_null=True
    )
    password_recovery_msg = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    sms_password_recovery = serializers.BooleanField(default=False)
    sms_provider = serializers.ChoiceField(
        choices=constants.SMS_BACKENDS, required=False, allow_null=True
    )

    # LDAP settings
    ldap_server_address = serializers.CharField(default="localhost")
    ldap_server_port = serializers.IntegerField(default=389)
    ldap_enable_secondary_server = serializers.BooleanField(default=False)
    ldap_secondary_server_address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    ldap_secondary_server_port = serializers.IntegerField(default=389, required=False)
    ldap_secured = serializers.ChoiceField(
        choices=constants.LDAP_SECURE_MODES, default="none"
    )
    ldap_is_active_directory = serializers.BooleanField(default=False)
    ldap_admin_groups = serializers.CharField(
        default="", required=False, allow_blank=True
    )
    ldap_group_type = serializers.ChoiceField(
        default="posixgroup", choices=constants.LDAP_GROUP_TYPES
    )
    ldap_groups_search_base = serializers.CharField(
        default="", required=False, allow_blank=True
    )
    ldap_password_attribute = serializers.CharField(default="userPassword")

    # LDAP auth settings
    ldap_auth_method = serializers.ChoiceField(
        choices=constants.LDAP_AUTH_METHODS,
        default="searchbind",
    )
    ldap_bind_dn = serializers.CharField(
        default="", required=False, allow_blank=True, allow_null=True
    )
    ldap_bind_password = serializers.CharField(
        default="", required=False, allow_blank=True, allow_null=True
    )
    ldap_search_base = serializers.CharField(
        default="", required=False, allow_blank=True
    )
    ldap_search_filter = serializers.CharField(
        default="(mail=%(user)s)", required=False, allow_blank=True
    )
    ldap_user_dn_template = serializers.CharField(
        default="", required=False, allow_blank=True
    )

    # LDAP sync settings
    ldap_sync_bind_dn = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    ldap_sync_bind_password = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    ldap_enable_sync = serializers.BooleanField(default=False)
    ldap_sync_delete_remote_account = serializers.BooleanField(default=False)
    ldap_sync_account_dn_template = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    ldap_enable_import = serializers.BooleanField(default=False)
    ldap_import_search_base = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    ldap_import_search_filter = serializers.CharField(default="(cn=*)", required=False)
    ldap_import_username_attr = serializers.CharField(default="cn")
    ldap_dovecot_sync = serializers.BooleanField(default=False)
    ldap_dovecot_conf_file = serializers.CharField(
        default="/etc/dovecot/dovecot-modoboa.conf", required=False
    )

    # Dashboard settings
    custom_welcome_message = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    rss_feed_url = serializers.URLField(
        allow_blank=True, required=False, allow_null=True
    )
    show_rss_feed_to_superadmins = serializers.BooleanField(default=False)
    hide_features_widget = serializers.BooleanField(default=False)

    # Theme settings
    theme_primary_color = serializers.CharField(default="#046BF8")
    theme_primary_color_dark = serializers.CharField(default="#0350BA")
    theme_primary_color_light = serializers.CharField(default="#3688F9")
    theme_secondary_color = serializers.CharField(default="#F18429")
    theme_label_color = serializers.CharField(default="#616161")
    theme_login_logo_url = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    theme_menu_logo_url = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    theme_creation_form_logo_url = serializers.CharField(
        required=False, allow_blank=True, default=""
    )

    # Notification settings
    sender_address = lib_fields.DRFEmailFieldUTF8(default="noreply@yourdomain.test")

    # API settings
    enable_api_communication = serializers.BooleanField(default=True)
    check_new_versions = serializers.BooleanField(default=True)
    send_new_versions_email = serializers.BooleanField(default=False)
    new_versions_email_rcpt = lib_fields.DRFEmailFieldUTF8(
        required=False, allow_null=True
    )
    send_statistics = serializers.BooleanField(default=True)

    # Misc settings
    enable_inactive_accounts = serializers.BooleanField(default=True)
    inactive_account_threshold = serializers.IntegerField(default=30)
    top_notifications_check_interval = serializers.IntegerField(default=30)
    log_maximum_age = serializers.IntegerField(default=365)
    message_history_maximum_age = serializers.IntegerField(default=180)
    items_per_page = serializers.IntegerField(default=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sms_backend_fields = sms_backends.get_all_backend_serializer_settings()
        for field, definition in sms_backend_fields.items():
            self.fields[field] = definition["type"](**definition["attrs"])
        # Populate choices of password_scheme
        self.fields["password_scheme"].choices = app_settings.get_password_scheme()

    def validate_ldap_user_dn_template(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError):
            raise serializers.ValidationError(_("Invalid syntax")) from None
        return value

    def validate_ldap_sync_account_dn_template(self, value):
        if value:
            try:
                value % {"user": "toto"}
            except (KeyError, ValueError):
                raise serializers.ValidationError(_("Invalid syntax")) from None
        return value

    def validate_ldap_search_filter(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError, TypeError):
            raise serializers.ValidationError(_("Invalid syntax")) from None
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
        errors = {}
        if data["sms_password_recovery"]:
            provider = data.get("sms_provider")
            if provider:
                sms_settings = sms_backends.get_backend_settings(provider)
                if sms_settings:
                    for name in sms_settings.keys():
                        if not data.get(name):
                            errors[name] = _("This field is required")
            else:
                errors["sms_provider"] = _("This field is required")

        if data["authentication_type"] == "ldap":
            if data["ldap_auth_method"] == "searchbind":
                required_fields = ["ldap_search_base", "ldap_search_filter"]
            else:
                required_fields = ["ldap_user_dn_template"]
            for f in required_fields:
                if data.get(f, "") == "":
                    errors[f] = _("This field is required")
        if len(errors):
            raise serializers.ValidationError(errors)
        return data

    def post_save(self, request):
        request.localconfig.need_dovecot_update = True
        request.localconfig.save(update_fields=["need_dovecot_update"])

    def _apply_ldap_settings(self, values, backend):
        """Apply configuration for given backend."""
        import ldap
        from django_auth_ldap.config import (
            LDAPSearch,
            PosixGroupType,
            GroupOfNamesType,
            ActiveDirectoryGroupType,
        )

        if not hasattr(settings, backend.setting_fullname("USER_ATTR_MAP")):
            setattr(
                settings,
                backend.setting_fullname("USER_ATTR_MAP"),
                {"first_name": "givenName", "email": "mail", "last_name": "sn"},
            )
        ldap_uri = "ldaps://" if values["ldap_secured"] == "ssl" else "ldap://"
        ldap_uri += f"{values[backend.srv_address_setting_name]}:{values[backend.srv_port_setting_name]}"
        setattr(settings, backend.setting_fullname("SERVER_URI"), ldap_uri)
        if values["ldap_secured"] == "starttls":
            setattr(settings, backend.setting_fullname("START_TLS"), True)

        if values["ldap_is_active_directory"]:
            setattr(
                settings,
                backend.setting_fullname("GROUP_TYPE"),
                ActiveDirectoryGroupType(),
            )
            searchfilter = "(objectClass=group)"
        elif values["ldap_group_type"] == "groupofnames":
            setattr(
                settings, backend.setting_fullname("GROUP_TYPE"), GroupOfNamesType()
            )
            searchfilter = "(objectClass=groupOfNames)"
        else:
            setattr(settings, backend.setting_fullname("GROUP_TYPE"), PosixGroupType())
            searchfilter = "(objectClass=posixGroup)"
        setattr(
            settings,
            backend.setting_fullname("GROUP_SEARCH"),
            LDAPSearch(
                values["ldap_groups_search_base"], ldap.SCOPE_SUBTREE, searchfilter
            ),
        )
        if values["ldap_auth_method"] == "searchbind":
            setattr(
                settings, backend.setting_fullname("BIND_DN"), values["ldap_bind_dn"]
            )
            setattr(
                settings,
                backend.setting_fullname("BIND_PASSWORD"),
                values["ldap_bind_password"],
            )
            search = LDAPSearch(
                values["ldap_search_base"],
                ldap.SCOPE_SUBTREE,
                values["ldap_search_filter"],
            )
            setattr(settings, backend.setting_fullname("USER_SEARCH"), search)
        else:
            setattr(
                settings,
                backend.setting_fullname("USER_DN_TEMPLATE"),
                values["ldap_user_dn_template"],
            )
            setattr(
                settings, backend.setting_fullname("BIND_AS_AUTHENTICATING_USER"), True
            )
        if values["ldap_is_active_directory"]:
            setting = backend.setting_fullname("GLOBAL_OPTIONS")
            if not hasattr(settings, setting):
                setattr(settings, setting, {ldap.OPT_REFERRALS: False})
            else:
                getattr(settings, setting)[ldap.OPT_REFERRALS] = False

    def to_django_settings(self):
        """Apply LDAP related parameters to Django settings.

        Doing so, we can use the django_auth_ldap module.
        """
        try:
            import ldap  # noqa

            ldap_available = True
        except ImportError:
            ldap_available = False

        values = dict(param_tools.get_global_parameters("core"))
        if not ldap_available or values["authentication_type"] != "ldap":
            return

        from modoboa.lib.authbackends import LDAPBackend

        self._apply_ldap_settings(values, LDAPBackend)

        if not values["ldap_enable_secondary_server"]:
            return

        from modoboa.lib.authbackends import LDAPSecondaryBackend

        self._apply_ldap_settings(values, LDAPSecondaryBackend)


class FIDOSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserFidoKey
        fields = ["id", "name", "added_on", "last_used", "use_count"]
        extra_kwargs = {
            "id": {"read_only": True},
            "added_on": {"read_only": True},
            "last_used": {"read_only": True},
            "use_count": {"read_only": True},
        }


class FidoRegistrationSerializer(serializers.Serializer):
    """Serializer used to finish the fido key registration."""

    type = serializers.CharField()
    id = serializers.CharField()
    rawId = serializers.CharField()
    authenticatorAttachment = serializers.CharField()
    response = serializers.JSONField()
    name = serializers.CharField()


class FidoAuthenticationSerializer(serializers.Serializer):
    """Serializer used to finish the fido key authentication."""

    authenticatorAttachment = serializers.CharField()
    clientExtensionResults = serializers.JSONField()
    id = serializers.CharField()
    rawId = serializers.CharField()
    response = serializers.JSONField()
    type = serializers.CharField()


class LogSerializer(serializers.ModelSerializer):
    """Log serializer."""

    date_created = serializers.SerializerMethodField()

    class Meta:
        model = models.Log
        fields = ("date_created", "message", "level", "logger")

    def get_date_created(self, log) -> str:
        return formats.date_format(log.date_created, "SHORT_DATETIME_FORMAT")


class VerifyTFACodeSerializer(serializers.Serializer):
    """Serializer used to verify 2FA code validity."""

    code = serializers.CharField()

    def validate_code(self, value):
        device = django_otp.match_token(self.context["user"], value)
        if device is None:
            raise serializers.ValidationError(_("This code is invalid"))
        return device


class CheckPasswordSerializer(serializers.Serializer):
    """Simple serializer to check user password."""

    password = serializers.CharField()

    def validate_password(self, value):
        user = self.context["user"]
        if not authenticate(username=user.username, password=value):
            raise serializers.ValidationError(_("Invalid password"))
        return value


class UserAPITokenSerializer(serializers.Serializer):
    """Serializer used by API access routes."""

    token = serializers.CharField()


class ModoboaComponentSerializer(serializers.Serializer):
    """Serializer used for information endpoint."""

    label = serializers.CharField()
    name = serializers.CharField()
    version = serializers.CharField()
    last_version = serializers.CharField(required=False)
    description = serializers.CharField()
    update = serializers.BooleanField(default=False)
    changelog_url = serializers.URLField(required=False)


class NotificationSerializer(serializers.Serializer):
    """Serializer used to render a notification."""

    id = serializers.CharField()
    text = serializers.CharField()
    color = serializers.CharField()
    target = serializers.CharField()
    url = serializers.CharField(required=False)
    counter = serializers.IntegerField(required=False)


class ModoboaApplicationSerializer(serializers.Serializer):
    label = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()
    url = serializers.CharField()
    description = serializers.CharField(required=False)


class NewsFeedEntrySerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.CharField()
    published = serializers.DateTimeField()


class ThemeSerializer(serializers.Serializer):
    theme_primary_color = serializers.CharField(default="#046BF8")
    theme_primary_color_dark = serializers.CharField(default="#0350BA")
    theme_primary_color_light = serializers.CharField(default="#3688F9")
    theme_secondary_color = serializers.CharField(default="#F18429")
    theme_label_color = serializers.CharField(default="#616161")
    theme_login_logo_url = serializers.CharField(default="", allow_blank=True)
    theme_menu_logo_url = serializers.CharField(default="", allow_blank=True)
    theme_creation_form_logo_url = serializers.CharField(default="", allow_blank=True)


class ThemeLogoUploadSerializer(serializers.Serializer):
    LOGO_TYPES = ("login", "menu", "creation_form")

    logo_type = serializers.ChoiceField(choices=LOGO_TYPES)
    image = serializers.ImageField()


class StatisticsSerializer(serializers.Serializer):
    domain_count = serializers.IntegerField()
    domain_alias_count = serializers.IntegerField()
    account_count = serializers.IntegerField()
    alias_count = serializers.IntegerField()


class FrontendMenuEntrySerializer(serializers.Serializer):
    """Serializer used to describe a menu entry exposed by a plugin."""

    label = serializers.CharField()
    icon = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    to = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    roles = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    category = serializers.ChoiceField(
        choices=[("admin", "admin"), ("user", "user"), ("account", "account")],
        required=False,
        default="admin",
    )
    children = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class FrontendRouteSerializer(serializers.Serializer):
    """Serializer used to describe a frontend route exposed by a plugin."""

    name = serializers.CharField()
    path = serializers.CharField()
    component = serializers.CharField()
    parent = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    meta = serializers.DictField(required=False, default=dict)
    props = serializers.DictField(required=False, default=dict)
    children = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class FrontendRemoteSerializer(serializers.Serializer):
    """Serializer describing a Module Federation remote exposed by a plugin."""

    name = serializers.CharField()
    url = serializers.CharField()
    format = serializers.ChoiceField(
        choices=[("esm", "esm"), ("systemjs", "systemjs"), ("var", "var")],
        required=False,
        default="esm",
    )


class FrontendUIExtensionPositionSerializer(serializers.Serializer):
    """Serializer describing where a UI extension item should be inserted."""

    after = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    before = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    at = serializers.IntegerField(required=False, allow_null=True)


class FrontendUIExtensionSerializer(serializers.Serializer):
    """Generic serializer for a UI extension descriptor.

    Plugin-specific shapes are validated against this loose schema; any
    extra keys declared by a plugin are passed through unchanged so that
    extension points can interpret them as needed on the frontend.
    """

    name = serializers.CharField()
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    component = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = FrontendUIExtensionPositionSerializer(required=False, allow_null=True)
    applies_to = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    props = serializers.DictField(required=False, default=dict)
    summary = serializers.DictField(required=False, default=dict)


class FrontendPluginManifestSerializer(serializers.Serializer):
    """Serializer used to expose a plugin manifest to the frontend."""

    name = serializers.CharField()
    label = serializers.CharField()
    remote = FrontendRemoteSerializer(required=False, allow_null=True)
    menu_entries = FrontendMenuEntrySerializer(many=True, default=list)
    routes = FrontendRouteSerializer(many=True, default=list)
    ui_extensions = serializers.DictField(
        child=FrontendUIExtensionSerializer(many=True), required=False, default=dict
    )
