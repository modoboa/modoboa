"""Core API v2 serializers."""

import django_otp
import oath

from django.db.models import Q

from django.contrib.auth import password_validation
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as djangoValidationError

from django.template import loader

from django.utils import formats
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy, gettext as _

from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from modoboa.core import (
    constants,
    models,
    sms_backends,
    app_settings,
    context_processors,
)
from modoboa.core.models import User
from modoboa.lib import fields as lib_fields, cryptutils


class CustomValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A server error occurred."

    def __init__(self, detail, status_code):
        if status_code is not None:
            self.status_code = status_code
        if detail is not None:
            self.detail = detail
        else:
            self.detail = {"detail": force_str(self.default_detail)}


class NoSMSAvailable(Exception):
    """Raised when no sms totp is available for password reset (to try email)."""

    pass


class PasswordRequirementsFailure(Exception):
    """Raised when django is not happy with password provided."""

    def __init__(self, message_list, *args: object) -> None:
        super().__init__(*args)
        self.message_list = message_list


class CoreGlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General settings
    authentication_type = serializers.ChoiceField(
        choices=[("local", gettext_lazy("Local")), ("ldap", "LDAP")], default="local"
    )
    password_scheme = serializers.ChoiceField(
        choices=[("sha512crypt", "sha512crypt")], required=False
    )
    rounds_number = serializers.IntegerField(default=70000)
    update_scheme = serializers.BooleanField(default=True)
    default_password = serializers.CharField(default="ChangeMe1!")
    random_password_length = serializers.IntegerField(min_value=8, default=8)
    update_password_url = serializers.URLField(required=False, allow_blank=True)
    password_recovery_msg = serializers.CharField(required=False, allow_blank=True)
    sms_password_recovery = serializers.BooleanField(default=False)
    sms_provider = serializers.ChoiceField(
        choices=constants.SMS_BACKENDS, required=False, allow_null=True
    )

    # LDAP settings
    ldap_server_address = serializers.CharField(default="localhost")
    ldap_server_port = serializers.IntegerField(default=389)
    ldap_enable_secondary_server = serializers.BooleanField(default=False)
    ldap_secondary_server_address = serializers.CharField(required=False)
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
    ldap_bind_dn = serializers.CharField(default="", required=False, allow_blank=True)
    ldap_bind_password = serializers.CharField(
        default="", required=False, allow_blank=True
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
    ldap_sync_bind_dn = serializers.CharField(required=False, allow_blank=True)
    ldap_sync_bind_password = serializers.CharField(required=False, allow_blank=True)
    ldap_enable_sync = serializers.BooleanField(default=False)
    ldap_sync_delete_remote_account = serializers.BooleanField(default=False)
    ldap_sync_account_dn_template = serializers.CharField(
        required=False, allow_blank=True
    )
    ldap_enable_import = serializers.BooleanField(default=False)
    ldap_import_search_base = serializers.CharField(required=False, allow_blank=True)
    ldap_import_search_filter = serializers.CharField(default="(cn=*)", required=False)
    ldap_import_username_attr = serializers.CharField(default="cn")
    ldap_dovecot_sync = serializers.BooleanField(default=False)
    ldap_dovecot_conf_file = serializers.CharField(
        default="/etc/dovecot/dovecot-modoboa.conf", required=False
    )

    # Dashboard settings
    rss_feed_url = serializers.URLField(
        allow_blank=True, required=False, allow_null=True
    )
    hide_features_widget = serializers.BooleanField(default=False)

    # Notification settings
    sender_address = lib_fields.DRFEmailFieldUTF8(default="noreply@yourdomain.test")

    # API settings
    enable_api_communication = serializers.BooleanField(default=True)
    check_new_versions = serializers.BooleanField(default=True)
    send_new_versions_email = serializers.BooleanField(default=False)
    new_versions_email_rcpt = lib_fields.DRFEmailFieldUTF8(required=False)
    send_statistics = serializers.BooleanField(default=True)

    # Misc settings
    enable_inactive_accounts = serializers.BooleanField(default=True)
    inactive_account_threshold = serializers.IntegerField(default=30)
    top_notifications_check_interval = serializers.IntegerField(default=30)
    log_maximum_age = serializers.IntegerField(default=365)
    items_per_page = serializers.IntegerField(default=30)
    default_top_redirection = serializers.ChoiceField(
        default="user", choices=[("user", _("User profile"))], required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sms_backend_fields = sms_backends.get_all_backend_serializer_settings()
        for field, definition in sms_backend_fields.items():
            self.fields[field] = definition["type"](**definition["attrs"])
        # Choices serializer for default_top_redirection field
        self.fields["default_top_redirection"].choices = (
            app_settings.enabled_applications()
        )
        # Populate choices of password_scheme
        self.fields["password_scheme"].choices = app_settings.get_password_scheme()

    def validate_ldap_user_dn_template(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError):
            raise serializers.ValidationError(_("Invalid syntax")) from None
        return value

    def validate_ldap_sync_account_dn_template(self, value):
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
        if not user.check_password(value):
            raise serializers.ValidationError(_("Invalid password"))
        return value


class UserAPITokenSerializer(serializers.Serializer):
    """Serializer used by API access routes."""

    token = serializers.CharField()


class PasswordRecoveryEmailSerializer(serializers.Serializer):
    """Serializer used by password recovery route."""

    email = serializers.EmailField()

    def validate(self, data):
        clean_email = data["email"]
        self.context["user"] = (
            User.objects.filter(email__iexact=clean_email, is_active=True).exclude(
                Q(secondary_email__isnull=True) | Q(secondary_email="")
            )
        ).first()
        if self.context["user"] is None:
            raise CustomValidationError(
                {"type": "email", "reason": "No valid user found."}, 404
            )
        return data

    def save(self):
        user = self.context["user"]
        to_email = user.secondary_email
        current_site = get_current_site(self.context["request"])
        site_name = current_site.name
        domain = current_site.domain
        context = {
            "email": to_email,
            "domain": domain,
            "site_name": site_name,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            "token": default_token_generator.make_token(user),
            "protocol": "https",
        }
        context.update(context_processors.new_admin_url())
        subject = loader.render_to_string(
            "registration/password_reset_subject.txt", context
        )
        # Email subject *must not* contain newlines
        subject = "".join(subject.splitlines())
        body = loader.render_to_string(
            "registration/password_reset_email_v2.html", context
        )
        send_mail(subject, body, None, [to_email], fail_silently=False)


def send_sms_code(secret, backend, user):
    """Send a sms containing a TOTP code for password reset."""
    code = oath.totp(secret)
    text = _(
        "Please use the following code to recover your Modoboa password: {}".format(
            code
        )
    )
    if not backend.send(text, [str(user.phone_number)]):
        raise NoSMSAvailable()


class PasswordRecoverySmsSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data, *args, **kwargs):
        request = self.context["request"]
        clean_email = data["email"]

        user = User.objects.filter(email__iexact=clean_email, is_active=True).first()
        if user is None:
            raise CustomValidationError(
                {"type": "sms", "reason": "No valid user found."}, 404
            )

        self.context["user"] = (
            User.objects.filter(email__iexact=clean_email, is_active=True).exclude(
                Q(phone_number__isnull=True) | Q(phone_number="")
            )
        ).first()
        if self.context["user"] is None:
            raise NoSMSAvailable()

        if not request.localconfig.parameters.get_value("sms_password_recovery"):
            raise NoSMSAvailable()

        user = self.context["user"]
        if not user:
            raise NoSMSAvailable()
        backend = sms_backends.get_active_backend(request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        send_sms_code(secret, backend, user)
        request.session["totp_secret"] = secret
        request.session["user_pk"] = user.pk
        return data


class PasswordRecoverySmsConfirmSerializer(serializers.Serializer):
    sms_totp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, data):
        try:
            self.context["totp_secret"] = self.context["request"].session["totp_secret"]
        except KeyError:
            raise CustomValidationError(
                {"reason": "totp secret not set in session"}, 403
            ) from None
        if not oath.accept_totp(self.context["totp_secret"], data["sms_totp"])[0]:
            raise CustomValidationError({"reason": "Wrong totp"}, 400)

        # Attempt to get user, will raise an error if pk is not valid
        self.context["user"] = User.objects.filter(
            pk=self.context["request"].session["user_pk"]
        ).first()
        if self.context["user"] is None:
            raise CustomValidationError({"reason": "Invalid user"}, 400)

        return data

    def save(self):
        self.context["request"].session.pop("totp_secret")
        user_pk = self.context["request"].session.pop("user_pk")
        token = default_token_generator.make_token(self.context["user"])
        uid = urlsafe_base64_encode(force_bytes(user_pk))
        self.context["response"] = (token, uid)
        return True


class PasswordRecoverySmsResendSerializer(serializers.Serializer):
    def validate(self, data):
        try:
            self.context["totp_secret"] = self.context["request"].session["totp_secret"]
        except KeyError:
            raise CustomValidationError(
                {"reason": "totp secret not set in session"}, status.HTTP_403_FORBIDDEN
            ) from None

        # Attempt to get user, will raise an error if pk is not valid
        self.context["user"] = User.objects.filter(
            pk=self.context["request"].session["user_pk"]
        ).first()
        if self.context["user"] is None:
            raise CustomValidationError({"reason": "Invalid user"}, 400)

        return data

    def save(self):
        backend = sms_backends.get_active_backend(
            self.context["request"].localconfig.parameters
        )
        send_sms_code(self.context["totp_secret"], backend, self.context["user"])
        return True


class PasswordRecoveryConfirmSerializer(serializers.Serializer):
    new_password1 = serializers.CharField()
    new_password2 = serializers.CharField()

    token = serializers.CharField()

    id = serializers.CharField()

    def get_user(self, user_id):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(user_id).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def validate(self, data):
        # Validate password
        if (
            data["new_password1"] == ""
            or data["new_password1"] != data["new_password2"]
        ):
            raise serializers.ValidationError("Password is empty or does not match")

        user = self.get_user(data["id"])

        if user is None:
            raise CustomValidationError({"reason": "User not found."}, 404)

        if not default_token_generator.check_token(user, data["token"]):
            raise CustomValidationError({"reason": "Wrong reset token"}, 403)

        # Check that the password works with set conditions
        try:
            password_validation.validate_password(data["new_password1"], user)
        except djangoValidationError as e:
            raise PasswordRequirementsFailure(e.messages) from None
        self.context["user"] = user
        return super().validate(data)

    def save(self):
        user = self.context["user"]
        user.set_password(self.validated_data["new_password1"])
        user.save()
        return True


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
    url = serializers.CharField(required=False)
    text = serializers.CharField()
    level = serializers.CharField()


class ModoboaApplicationSerializer(serializers.Serializer):

    label = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()
    url = serializers.CharField()
    description = serializers.CharField(required=False)
