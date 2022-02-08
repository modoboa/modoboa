"""Admin API v2 serializers."""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import validators as dj_validators
from django.utils.translation import ugettext as _

from django.contrib.auth import password_validation

from rest_framework import serializers

from modoboa.admin.api.v1 import serializers as v1_serializers
from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib import fields as lib_fields
from modoboa.lib import validators, web_utils
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools

from ... import constants, models


class CreateDomainAdminSerializer(serializers.Serializer):
    """Sub serializer for domain administrator creation."""

    username = serializers.CharField()
    password = serializers.CharField(required=False)
    with_mailbox = serializers.BooleanField(default=False)
    with_aliases = serializers.BooleanField(default=False)


class DomainSerializer(v1_serializers.DomainSerializer):
    """Domain serializer for v2 API."""

    domain_admin = CreateDomainAdminSerializer(required=False)

    class Meta(v1_serializers.DomainSerializer.Meta):
        fields = v1_serializers.DomainSerializer.Meta.fields + (
            "domain_admin",
        )

    def create(self, validated_data):
        """Create administrator and other stuff if needed."""
        domain_admin = validated_data.pop("domain_admin", None)
        domain = super().create(validated_data)
        if not domain_admin:
            return domain

        # 1. Create a domain administrator
        username = "%s@%s" % (domain_admin["username"], domain.name)
        try:
            da = core_models.User.objects.get(username=username)
        except core_models.User.DoesNotExist:
            pass
        else:
            raise lib_exceptions.Conflict(
                _("User '%s' already exists") % username)
        user = self.context["request"].user
        core_signals.can_create_object.send(
            self.__class__, context=user, klass=models.Mailbox)
        da = core_models.User(username=username, email=username, is_active=True)
        password = domain_admin.get("password")
        if password is None:
            password = param_tools.get_global_parameter(
                "default_password", app="core")
        da.set_password(password)
        da.save()
        da.role = "DomainAdmins"
        da.post_create(user)

        # 2. Create mailbox if needed
        if domain_admin["with_mailbox"]:
            dom_admin_username = domain_admin["username"]
            mb = models.Mailbox(
                address=dom_admin_username, domain=domain,
                user=da, use_domain_quota=True
            )
            mb.set_quota(
                override_rules=user.has_perm("admin.change_domain"))
            mb.save(creator=user)

            # 3. Create aliases if needed
            condition = (
                domain.type == "domain" and
                domain_admin["with_aliases"] and
                dom_admin_username != "postmaster"
            )
            if condition:
                core_signals.can_create_object.send(
                    self.__class__, context=user, klass=models.Alias)
                address = u"postmaster@{}".format(domain.name)
                alias = models.Alias.objects.create(
                    address=address, domain=domain, enabled=True)
                alias.set_recipients([mb.full_address])
                alias.post_create(user)

        domain.add_admin(da)
        return domain


class DeleteDomainSerializer(serializers.Serializer):
    """Serializer used with delete operation."""

    keep_folder = serializers.BooleanField(default=False)


class AdminGlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # Domain settings
    enable_mx_checks = serializers.BooleanField(default=True)
    valid_mxs = serializers.CharField(allow_blank=True)
    domains_must_have_authorized_mx = serializers.BooleanField(default=False)
    enable_spf_checks = serializers.BooleanField(default=True)
    enable_dkim_checks = serializers.BooleanField(default=True)
    enable_dmarc_checks = serializers.BooleanField(default=True)
    enable_autoconfig_checks = serializers.BooleanField(default=True)
    custom_dns_server = serializers.IPAddressField(allow_blank=True)
    enable_dnsbl_checks = serializers.BooleanField(default=True)
    dkim_keys_storage_dir = serializers.CharField(allow_blank=True)
    dkim_default_key_length = serializers.ChoiceField(
        default=2048, choices=constants.DKIM_KEY_LENGTHS)
    default_domain_quota = serializers.IntegerField(default=0)
    default_domain_message_limit = serializers.IntegerField(
        required=False, allow_null=True)

    # Mailboxes settings
    handle_mailboxes = serializers.BooleanField(default=False)
    default_mailbox_quota = serializers.IntegerField(default=0)
    default_mailbox_message_limit = serializers.IntegerField(
        required=False, allow_null=True)
    auto_account_removal = serializers.BooleanField(default=False)
    auto_create_domain_and_mailbox = serializers.BooleanField(default=True)
    create_alias_on_mbox_rename = serializers.BooleanField(default=False)

    def validate_default_domain_quota(self, value):
        """Ensure quota is a positive integer."""
        if value < 0:
            raise serializers.ValidationError(
                _("Must be a positive integer")
            )
        return value

    def validate_default_mailbox_quota(self, value):
        """Ensure quota is a positive integer."""
        if value < 0:
            raise serializers.ValidationError(
                _("Must be a positive integer")
            )
        return value

    def validate_dkim_keys_storage_dir(self, value):
        """Check that directory exists."""
        if value:
            if not os.path.isdir(value):
                raise serializers.ValidationError(
                    _("Directory not found.")
                )
            code, output = exec_cmd("which openssl")
            if code:
                raise serializers.ValidationError(
                    _("openssl not found, please make sure it is installed.")
                )
        return value

    def validate(self, data):
        """Check MX options."""
        condition = (
            data.get("enable_mx_checks") and
            data.get("domains_must_have_authorized_mx") and
            not data.get("valid_mxs"))
        if condition:
            raise serializers.ValidationError({
                "valid_mxs": _("Define at least one authorized network / address")
            })
        return data


class DomainAdminSerializer(serializers.ModelSerializer):
    """Serializer used for administrator related routes."""

    class Meta:
        model = core_models.User
        fields = ("id", "username", "first_name", "last_name")


class SimpleDomainAdminSerializer(serializers.Serializer):
    """Serializer used for add/remove operations."""

    account = serializers.PrimaryKeyRelatedField(
        queryset=core_models.User.objects.all()
    )


class TagSerializer(serializers.Serializer):
    """Serializer used to represent a tag."""

    name = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField()


class IdentitySerializer(serializers.Serializer):
    """Serializer used for identities."""

    pk = serializers.IntegerField()
    type = serializers.CharField()
    identity = serializers.CharField()
    name_or_rcpt = serializers.CharField()
    tags = TagSerializer(many=True)


class MailboxSerializer(serializers.ModelSerializer):
    """Base mailbox serializer."""

    quota = serializers.CharField(required=False)

    class Meta:
        model = models.Mailbox
        fields = (
            "pk", "use_domain_quota", "quota", "message_limit"
        )

    def validate_quota(self, value):
        """Convert quota to MB."""
        return web_utils.size2integer(value, output_unit="MB")

    def validate(self, data):
        """Check if quota is required."""
        method = self.context["request"].method
        if not data.get("use_domain_quota", False):
            if "quota" not in data and method != "PATCH":
                raise serializers.ValidationError({
                    "quota": _("This field is required")
                })
        return data


class WritableAccountSerializer(v1_serializers.WritableAccountSerializer):
    """Add support for aliases and sender addresses."""

    aliases = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8(),
        required=False
    )
    mailbox = MailboxSerializer(required=False)

    class Meta(v1_serializers.WritableAccountSerializer.Meta):
        fields = tuple(
            field
            for field in v1_serializers.WritableAccountSerializer.Meta.fields
            if field != "random_password"
        ) + ("aliases", )

    def validate_aliases(self, value):
        """Check if required domains are locals and user can access them."""
        aliases = []
        for alias in value:
            localpart, domain = models.validate_alias_address(
                alias, self.context["request"].user)
            aliases.append({"localpart": localpart, "domain": domain})
        return aliases

    def validate(self, data):
        """Check constraints."""
        master_user = data.get("master_user", False)
        role = data.get("role")
        if master_user and role != "SuperAdmins":
            raise serializers.ValidationError({
                "master_user": _("Not allowed for this role.")
            })
        if role == "SimpleUsers":
            username = data.get("username")
            if username:
                try:
                    validators.UTF8EmailValidator()(username)
                except ValidationError as err:
                    raise ValidationError({"username": err.message})
            mailbox = data.get("mailbox")
            if mailbox is None:
                if not self.instance:
                    data["mailbox"] = {
                        "use_domain_quota": True
                    }
        if data.get("password") or not self.partial:
            password = data.get("password")
            if password:
                try:
                    password_validation.validate_password(
                        data["password"], self.instance)
                except ValidationError as exc:
                    raise serializers.ValidationError({
                        "password": exc.messages[0]})
            elif not self.instance:
                raise serializers.ValidationError({
                    "password": _("This field is required.")
                })
        aliases = data.get("aliases")
        if aliases and "mailbox" not in data:
            raise serializers.ValidationError({
                "aliases": _("A mailbox is required to create aliases.")
            })
        domain_names = data.get("domains")
        if not domain_names:
            return data
        domains = []
        for name in domain_names:
            domain = models.Domain.objects.filter(name=name).first()
            if domain:
                domains.append(domain)
                continue
            raise serializers.ValidationError({
                "domains": _("Local domain {} does not exist").format(name)
            })
        data["domains"] = domains
        return data

    def create(self, validated_data):
        """Create account, mailbox and aliases."""
        creator = self.context["request"].user
        mailbox_data = validated_data.pop("mailbox", None)
        role = validated_data.pop("role")
        domains = validated_data.pop("domains", [])
        aliases = validated_data.pop("aliases", None)
        user = core_models.User(**validated_data)
        password = validated_data.pop("password")
        user.set_password(password)
        if "language" not in validated_data:
            user.language = settings.LANGUAGE_CODE
        user.save(creator=creator)
        if mailbox_data:
            mailbox_data["full_address"] = user.username
            self._create_mailbox(creator, user, mailbox_data)
        user.role = role
        self.set_permissions(user, domains)
        if aliases:
            for alias in aliases:
                models.Alias.objects.create(
                    creator=creator,
                    domain=alias["domain"],
                    address="{}@{}".format(alias["localpart"], alias["domain"]),
                    recipients=[user.username]
                )
        return user

    def update(self, instance, validated_data):
        """Update account and associated objects."""
        mailbox_data = validated_data.pop("mailbox", None)
        password = validated_data.pop("password", None)
        domains = validated_data.pop("domains", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        if mailbox_data:
            creator = self.context["request"].user
            if hasattr(instance, "mailbox"):
                if "username" in validated_data:
                    mailbox_data["email"] = validated_data["username"]
                    instance.email = validated_data["username"]
                instance.mailbox.update_from_dict(creator, mailbox_data)
            elif "username" in validated_data:
                mailbox_data["full_address"] = validated_data["username"]
                instance.email = validated_data["username"]
                self._create_mailbox(creator, instance, mailbox_data)
        instance.save()
        self.set_permissions(instance, domains)
        return instance


class DeleteAccountSerializer(serializers.Serializer):
    """Serializer used with delete operation."""

    keepdir = serializers.BooleanField(default=False)


class AliasSerializer(v1_serializers.AliasSerializer):
    """Alias serializer for v2 API."""

    class Meta(v1_serializers.AliasSerializer.Meta):
        # We remove 'internal' field
        fields = tuple(
            field
            for field in v1_serializers.AliasSerializer.Meta.fields
            if field != "internal"
        ) + ("expire_at", "description")


class UserForwardSerializer(serializers.Serializer):
    """Serializer to define user forward."""

    recipients = serializers.CharField(required=False)
    keepcopies = serializers.BooleanField(default=False)

    def validate_recipients(self, value):
        value = value.strip()
        recipients = []
        if not value:
            return recipients
        for recipient in value.split(","):
            dj_validators.validate_email(recipient)
            recipients.append(recipient)
        return recipients
