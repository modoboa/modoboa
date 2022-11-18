"""Core API v2 serializers."""
import oath
from django.utils import formats
from django.utils.translation import ugettext_lazy, ugettext as _

from django.db.models import Q

from django.contrib.auth import password_validation
from django.template import loader
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email

import django_otp
from rest_framework import serializers
from rest_framework.exceptions import APIException

from modoboa.lib import fields as lib_fields, cryptutils
from modoboa.core.models import User

from ... import constants
from ... import models
from ... import sms_backends
from ... import app_settings


class NoSMSAvailible(Exception):
    """ Raised when no sms totp is availible for password reset (to try email)."""
    pass


class NoUserFound(Exception):
    """ Raised when no valid user has been found (to have a proper 404 http code instead of 400."""
    pass


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
    update_scheme = serializers.BooleanField(default=True)
    default_password = serializers.CharField(default="password")
    random_password_length = serializers.IntegerField(min_value=8, default=8)
    update_password_url = serializers.URLField(required=False, allow_blank=True)
    password_recovery_msg = serializers.CharField(
        required=False, allow_blank=True)
    sms_password_recovery = serializers.BooleanField(default=False)
    sms_provider = serializers.ChoiceField(
        choices=constants.SMS_BACKENDS, required=False, allow_null=True)

    # LDAP settings
    ldap_server_address = serializers.CharField(default="localhost")
    ldap_server_port = serializers.IntegerField(default=389)
    ldap_enable_secondary_server = serializers.BooleanField(default=False)
    ldap_secondary_server_address = serializers.CharField(required=False)
    ldap_secondary_server_port = serializers.IntegerField(
        default=389, required=False)
    ldap_secured = serializers.ChoiceField(
        choices=constants.LDAP_SECURE_MODES,
        default="none"
    )
    ldap_is_active_directory = serializers.BooleanField(default=False)
    ldap_admin_groups = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_group_type = serializers.ChoiceField(
        default="posixgroup",
        choices=constants.LDAP_GROUP_TYPES
    )
    ldap_groups_search_base = serializers.CharField(
        default="", required=False, allow_blank=True)
    ldap_password_attribute = serializers.CharField(default="userPassword")

    # LDAP auth settings
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

    # LDAP sync settings
    ldap_sync_bind_dn = serializers.CharField(required=False, allow_blank=True)
    ldap_sync_bind_password = serializers.CharField(
        required=False, allow_blank=True)
    ldap_enable_sync = serializers.BooleanField(default=False)
    ldap_sync_delete_remote_account = serializers.BooleanField(default=False)
    ldap_sync_account_dn_template = serializers.CharField(
        required=False, allow_blank=True)
    ldap_enable_import = serializers.BooleanField(default=False)
    ldap_import_search_base = serializers.CharField(
        required=False, allow_blank=True)
    ldap_import_search_filter = serializers.CharField(
        default="(cn=*)", required=False
    )
    ldap_import_username_attr = serializers.CharField(default="cn")
    ldap_dovecot_sync = serializers.BooleanField(default=False)
    ldap_dovecot_conf_file = serializers.CharField(
        default="/etc/dovecot/dovecot-modoboa.conf", required=False
    )

    # Dashboard settings
    rss_feed_url = serializers.URLField(
        allow_blank=True, required=False, allow_null=True)
    hide_features_widget = serializers.BooleanField(default=False)

    # Notification settings
    sender_address = lib_fields.DRFEmailFieldUTF8(
        default="noreply@yourdomain.test")

    # API settings
    enable_api_communication = serializers.BooleanField(default=True)
    check_new_versions = serializers.BooleanField(default=True)
    send_new_versions_email = serializers.BooleanField(default=False)
    new_versions_email_rcpt = lib_fields.DRFEmailFieldUTF8(required=False)
    send_statistics = serializers.BooleanField(default=True)

    # Misc settings
    inactive_account_threshold = serializers.IntegerField(default=30)
    top_notifications_check_interval = serializers.IntegerField(default=30)
    log_maximum_age = serializers.IntegerField(default=365)
    items_per_page = serializers.IntegerField(default=30)
    default_top_redirection = serializers.ChoiceField(
        default="user", choices=[("user", _("User profile"))], required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sms_backend_fields = sms_backends.get_all_backend_serializer_settings()
        for field, definition in sms_backend_fields.items():
            self.fields[field] = definition["type"](
                **definition["attrs"])
        # Choices serializer for default_top_redirection field
        self.fields["default_top_redirection"].choices = app_settings.enabled_applications()

    def validate_ldap_user_dn_template(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError):
            raise serializers.ValidationError(_("Invalid syntax"))
        return value

    def validate_ldap_sync_account_dn_template(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError):
            raise serializers.ValidationError(_("Invalid syntax"))
        return value

    def validate_ldap_search_filter(self, value):
        try:
            value % {"user": "toto"}
        except (KeyError, ValueError, TypeError):
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


class EmailPasswordRecoveryInitSerializer(serializers.Serializer):
    """Serializer used by password recovery route."""

    email = serializers.EmailField()

    def validate(self, data):
        if not validate_email(data["email"]):
            clean_email = data["email"]

        self.context["user"] = (User.objects.filter(
            email__iexact=clean_email, is_active=True)
            .exclude(Q(secondary_email__isnull=True) | Q(secondary_email=""))
        ).first()
        if self.context["user"] is None:
            raise NoUserFound()
        return data

    def save(self):
        user = self.context["user"]
        to_email = user.secondary_email
        current_site = get_current_site(self.context["request"])
        site_name = current_site.name
        domain = current_site.domain
        context = {
            'email': to_email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user),
            'protocol': 'https',
        }
        subject = loader.render_to_string(
            "registration/password_reset_subject.txt", context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(
            "registration/password_reset_email_v2.html", context)

        if send_mail(subject, body, None, [to_email]) == 0:
            raise APIException("Email failed to send", 502)


class SMSPasswordRecoveryInitSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate(self, data, *args, **kwargs):
        request = self.context["request"]

        if not validate_email(data["email"]):
            clean_email = data["email"]

        self.context["user"] = (User.objects.filter(
            email__iexact=clean_email, is_active=True)
            .exclude(Q(phone_number__isnull=True) | Q(phone_number=""))
        ).first()
        if self.context["user"] is None:
            raise NoSMSAvailible()

        if not request.localconfig.parameters.get_value("sms_password_recovery"):
            raise NoSMSAvailible()

        user = self.context["user"]
        if not user:
            raise NoSMSAvailible()
        backend = sms_backends.get_active_backend(
            request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}"
            .format(code)
        )
        if not backend.send(text, [str(user.phone_number)]):
            raise NoSMSAvailible()
        request.session["totp_secret"] = secret
        request.session["user_pk"] = user.pk
        return data


class PasswordRecoverySmsSerializer(serializers.Serializer):

    sms_totp = serializers.CharField()

    def validate(self, data):

        if len(data['sms_totp']) != 6:
            raise serializers.ValidationError(
                "Wrong totp, try resend")

        try:
            totp_secret = self.context["request"].session["totp_secret"]
            self.context["request"].session.pop("totp_secret")
        except KeyError:
            raise serializers.ValidationError(
                "totp secret not set in session", 403)

        if not oath.accept_totp(totp_secret, data["sms_totp"]):
            raise serializers.ValidationError("Wrong totp", 403)

        self.user = get_user_model()._default_manager.get(
            pk=self.context["user_pk"])

        return data

    def save(self):
        self.context["request"].session.pop("totp_secret")
        self.context["request"].session.pop("user")
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.context["response"] = (token, uid)
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
            user = get_user_model()._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None
        return user

    def validate(self, data):

        # Validate password
        if data["new_password1"] == "" or data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError(
                "Password empty or doesn't not correspond")

        user = self.get_user(data["id"])

        password_validation.validate_password(data["new_password1"], user)

        if user is None:
            raise serializers.ValidationError("User not found", 404)

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError("Token not valid", 403)

        self.context["user"] = user
        return super().validate(data)

    def save(self):
        user = self.context["user"]
        user.set_password(self.validated_data["new_password1"])
        user.save()
        return True


class PasswordRecoverySmsResendSerializer(serializers.Serializer):

    def validate(self, data):

        try:
            self.context["session"].user_pk
            self.context["session"].totp_token
            return data
        except KeyError:
            raise serializers.ValidationError("paylaod not right", 403)

    def save(self):
        user = get_user_model()._default_manager.get(
            pk=self.context["session"].user_pk)
        request = self.context["request"]
        backend = sms_backends.get_active_backend(
            request.localconfig.parameters)
        secret = cryptutils.random_hex_key(20)
        code = oath.totp(secret)
        text = _(
            "Please use the following code to recover your Modoboa password: {}"
            .format(code)
        )
        if not backend.send(text, [str(user.phone_number)]):
            return False
        request.session["totp_secret"] = secret
        request.session["user_pk"] = user.pk
