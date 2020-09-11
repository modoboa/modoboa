"""Admin serializers."""

from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _, ugettext_lazy

from rest_framework import serializers

from modoboa.admin import models as admin_models
from modoboa.core import (
    constants as core_constants, models as core_models, signals as core_signals
)
from modoboa.lib import (
    email_utils, exceptions as lib_exceptions, fields as lib_fields,
    permissions, web_utils
)
from modoboa.parameters import tools as param_tools
from . import lib, models


class DomainSerializer(serializers.ModelSerializer):
    """Base Domain serializer."""

    quota = serializers.CharField(
        required=False,
        help_text=ugettext_lazy(
            "Quota shared between mailboxes. Can be expressed in KB, "
            "MB (default) or GB. A value of 0 means no quota."
        )
    )
    default_mailbox_quota = serializers.CharField(
        required=False,
        help_text=ugettext_lazy(
            "Default quota in MB applied to mailboxes. A value of 0 means "
            "no quota."
        )
    )

    class Meta:
        model = models.Domain
        fields = (
            "pk", "name", "quota", "default_mailbox_quota", "enabled", "type",
            "enable_dkim", "dkim_key_selector", "dkim_key_length",
            "dkim_public_key", "dkim_private_key_path",
            "mailbox_count", "mbalias_count", "domainalias_count",
            "message_limit"
        )
        read_only_fields = (
            "pk", "mailbox_count", "mbalias_count", "domainalias_count"
        )

    def validate_name(self, value):
        """Check name constraints."""
        domains_must_have_authorized_mx = (
            param_tools.get_global_parameter("domains_must_have_authorized_mx")
        )
        user = self.context["request"].user
        value = value.lower()
        if domains_must_have_authorized_mx and not user.is_superuser:
            if not lib.domain_has_authorized_mx(value):
                raise serializers.ValidationError(
                    _("No authorized MX record found for this domain"))
        return value

    def validate_quota(self, value):
        """Convert quota to MB."""
        return web_utils.size2integer(value, output_unit="MB")

    def validate_default_mailbox_quota(self, value):
        """Convert quota to MB."""
        return web_utils.size2integer(value, output_unit="MB")

    def validate(self, data):
        """Check quota values."""
        quota = data.get("quota", 0)
        default_mailbox_quota = data.get("default_mailbox_quota", 0)
        if quota != 0 and default_mailbox_quota > quota:
            raise serializers.ValidationError({
                "default_mailbox_quota":
                _("Cannot be greater than domain quota")
            })
        return data

    def create(self, validated_data):
        """Set permissions."""
        params = dict(param_tools.get_global_parameters("admin"))
        domain = models.Domain(**validated_data)
        condition = (
            params["default_domain_message_limit"] is not None and
            "message_limit" not in validated_data
        )
        if condition:
            domain.message_limit = params["default_domain_message_limit"]
        creator = self.context["request"].user
        core_signals.can_create_object.send(
            sender=self.__class__, context=creator,
            klass=models.Domain, instance=domain)
        domain.save(creator=creator)
        return domain


class DomainAliasSerializer(serializers.ModelSerializer):
    """Base DomainAlias serializer."""

    class Meta:
        model = admin_models.DomainAlias
        fields = ("pk", "name", "target", "enabled", )

    def validate_target(self, value):
        """Check target domain."""
        if not self.context["request"].user.can_access(value):
            raise serializers.ValidationError(_("Permission denied."))
        return value

    def validate_name(self, value):
        """Lower case name."""
        return value.lower()

    def create(self, validated_data):
        """Custom creation."""
        domain_alias = models.DomainAlias(**validated_data)
        creator = self.context["request"].user
        try:
            core_signals.can_create_object.send(
                sender=self.__class__, context=creator,
                klass=models.DomainAlias)
            core_signals.can_create_object.send(
                sender=self.__class__, context=domain_alias.target,
                object_type="domain_aliases")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError({
                "domain": force_text(inst)})
        domain_alias.save(creator=creator)
        return domain_alias


class MailboxSerializer(serializers.ModelSerializer):
    """Base mailbox serializer."""

    full_address = lib_fields.DRFEmailFieldUTF8()
    quota = serializers.CharField()

    class Meta:
        model = models.Mailbox
        fields = (
            "pk", "full_address", "use_domain_quota", "quota", "message_limit"
        )

    def validate_full_address(self, value):
        """Lower case address."""
        return value.lower()

    def validate_quota(self, value):
        """Convert quota to MB."""
        return web_utils.size2integer(value, output_unit="MB")


class AccountSerializer(serializers.ModelSerializer):
    """Base account serializer."""

    role = serializers.SerializerMethodField()
    mailbox = MailboxSerializer(required=False)
    domains = serializers.SerializerMethodField(
        help_text=_(
            "List of administered domains (resellers and domain "
            "administrators only)."))

    class Meta:
        model = core_models.User
        fields = (
            "pk", "username", "first_name", "last_name", "is_active",
            "master_user", "mailbox", "role", "language", "phone_number",
            "secondary_email", "domains",
        )

    def __init__(self, *args, **kwargs):
        """Adapt fields to current user."""
        super(AccountSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if not request:
            return
        user = self.context["request"].user
        if not user.is_superuser:
            del self.fields["master_user"]

    def get_role(self, account):
        """Return role."""
        return account.role

    def get_domains(self, account):
        """Return domains administered by this account."""
        if account.role not in ["DomainAdmins", "Resellers"]:
            return []
        return admin_models.Domain.objects.get_for_admin(account).values_list(
            "name", flat=True)


class AccountExistsSerializer(serializers.Serializer):
    """Simple serializer used with existence checks."""

    exists = serializers.BooleanField()


class AccountPasswordSerializer(serializers.ModelSerializer):

    """A serializer used to change a user password."""

    new_password = serializers.CharField()

    class Meta:
        model = core_models.User
        fields = (
            "password", "new_password", )

    def validate_password(self, value):
        """Check password."""
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Password not correct")
        return value

    def validate_new_password(self, value):
        """Check new password."""
        try:
            password_validation.validate_password(value, self.instance)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value

    def update(self, instance, validated_data):
        """Set new password."""
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


class WritableAccountSerializer(AccountSerializer):
    """Serializer to create account."""

    random_password = serializers.BooleanField(default=False)
    role = serializers.ChoiceField(choices=core_constants.ROLES)
    password = serializers.CharField(required=False)

    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + (
            "password", "random_password")

    def __init__(self, *args, **kwargs):
        """Adapt fields to current user."""
        super(WritableAccountSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")
        if not request:
            return
        user = self.context["request"].user
        self.fields["role"] = serializers.ChoiceField(
            choices=permissions.get_account_roles(user))
        self.fields["domains"] = serializers.ListField(
            child=serializers.CharField(), allow_empty=False, required=False)

    def validate_username(self, value):
        """Lower case username."""
        return value.lower()

    def validate(self, data):
        """Check constraints."""
        master_user = data.get("master_user", False)
        role = data.get("role")
        if master_user and role != "SuperAdmins":
            raise serializers.ValidationError({
                "master_user": _("Not allowed for this role.")
            })
        if role == "SimpleUsers":
            mailbox = data.get("mailbox")
            if mailbox is None:
                if not self.instance:
                    data["mailbox"] = {
                        "full_address": data["username"],
                        "use_domain_quota": True
                    }
            elif mailbox["full_address"] != data["username"]:
                raise serializers.ValidationError({
                    "username": _("Must be equal to mailbox full_address")
                })
        if not data.get("random_password"):
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
        domain_names = data.get("domains")
        if not domain_names:
            return data
        domains = []
        for name in domain_names:
            domain = admin_models.Domain.objects.filter(name=name).first()
            if domain:
                domains.append(domain)
                continue
            raise serializers.ValidationError({
                "domains": _("Local domain {} does not exist").format(name)
            })
        data["domains"] = domains
        return data

    def _create_mailbox(self, creator, account, data):
        """Create a new Mailbox instance."""
        full_address = data.pop("full_address")
        address, domain_name = email_utils.split_mailbox(full_address)
        domain = get_object_or_404(
            admin_models.Domain, name=domain_name)
        if not creator.can_access(domain):
            raise serializers.ValidationError({
                "domain": _("Permission denied.")})
        try:
            core_signals.can_create_object.send(
                sender=self.__class__, context=creator,
                klass=admin_models.Mailbox)
            core_signals.can_create_object.send(
                sender=self.__class__, context=domain,
                object_type="mailboxes")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError({
                "domain": force_text(inst)})
        quota = data.pop("quota", None)
        mb = admin_models.Mailbox(
            user=account, address=address, domain=domain, **data)
        mb.set_quota(quota, creator.has_perm("admin.add_domain"))
        default_msg_limit = param_tools.get_global_parameter(
            "default_mailbox_message_limit")
        if default_msg_limit is not None:
            mb.message_limit = default_msg_limit
        mb.save(creator=creator)
        account.email = full_address
        return mb

    def set_permissions(self, account, domains):
        """Assign permissions on domain(s)."""
        if account.role not in ["DomainAdmins", "Resellers"]:
            return
        current_domains = admin_models.Domain.objects.get_for_admin(account)
        for domain in current_domains:
            if domain not in domains:
                domain.remove_admin(account)
            else:
                domains.remove(domain)
        for domain in domains:
            domain.add_admin(account)

    def create(self, validated_data):
        """Create appropriate objects."""
        creator = self.context["request"].user
        mailbox_data = validated_data.pop("mailbox", None)
        role = validated_data.pop("role")
        domains = validated_data.pop("domains", [])
        random_password = validated_data.pop("random_password", False)
        user = core_models.User(**validated_data)
        if random_password:
            password = lib.make_password()
        else:
            password = validated_data.pop("password")
        user.set_password(password)
        if "language" not in validated_data:
            user.language = settings.LANGUAGE_CODE
        user.save(creator=creator)
        if mailbox_data:
            self._create_mailbox(creator, user, mailbox_data)
        user.role = role
        self.set_permissions(user, domains)
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
            if instance.mailbox:
                if "full_address" in mailbox_data:
                    # FIXME: compat, to remove ASAP.
                    mailbox_data["email"] = mailbox_data["full_address"]
                    instance.email = mailbox_data["full_address"]
                instance.mailbox.update_from_dict(creator, mailbox_data)
            else:
                self._create_mailbox(creator, instance, mailbox_data)
        instance.save()
        self.set_permissions(instance, domains)
        return instance


class AliasSerializer(serializers.ModelSerializer):
    """Base Alias serializer."""

    address = lib_fields.DRFEmailFieldUTF8AndEmptyUser()
    recipients = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8AndEmptyUser(),
        allow_empty=False,
        help_text=ugettext_lazy("A list of recipient"))

    class Meta:
        model = admin_models.Alias
        fields = ("pk", "address", "enabled", "internal", "recipients")

    def validate_address(self, value):
        """Check domain."""
        local_part, domain = email_utils.split_mailbox(value)
        self.domain = admin_models.Domain.objects.filter(name=domain).first()
        if self.domain is None:
            raise serializers.ValidationError(_("Domain not found."))
        if not self.context["request"].user.can_access(self.domain):
            raise serializers.ValidationError(_("Permission denied."))
        return value

    def create(self, validated_data):
        """Create appropriate objects."""
        creator = self.context["request"].user
        try:
            core_signals.can_create_object.send(
                sender=self.__class__, context=creator,
                klass=admin_models.Alias)
            core_signals.can_create_object.send(
                sender=self.__class__, context=self.domain,
                object_type="mailbox_aliases")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError(force_text(inst))
        recipients = validated_data.pop("recipients", None)
        alias = admin_models.Alias(domain=self.domain, **validated_data)
        alias.save(creator=creator)
        alias.set_recipients(recipients)
        return alias

    def update(self, instance, validated_data):
        """Update objects."""
        recipients = validated_data.pop("recipients", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        instance.set_recipients(recipients)
        return instance


class SenderAddressSerializer(serializers.ModelSerializer):
    """Base Alias serializer."""

    address = lib_fields.DRFEmailFieldUTF8AndEmptyUser()

    class Meta:
        model = admin_models.SenderAddress
        fields = ("pk", "address", "mailbox")

    def validate_address(self, value):
        """Check domain."""
        local_part, domain = email_utils.split_mailbox(value)
        domain = admin_models.Domain.objects.filter(name=domain).first()
        user = self.context["request"].user
        if domain and not user.can_access(domain):
            raise serializers.ValidationError(
                _("You don't have access to this domain."))
        return value

    def validate_mailbox(self, value):
        """Check permission."""
        user = self.context["request"].user
        if not user.can_access(value):
            raise serializers.ValidationError(
                _("You don't have access to this mailbox."))
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer by the reset password endpoint."""

    email = lib_fields.DRFEmailFieldUTF8()
