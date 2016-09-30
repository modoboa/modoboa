"""Admin serializers."""

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import serializers
from passwords import validators

from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
from modoboa.core import signals as core_signals
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib import permissions, email_utils, fields as lib_fields

from . import models


class DomainSerializer(serializers.ModelSerializer):

    """Base Domain serializer."""

    class Meta:
        model = models.Domain
        fields = ("pk", "name", "quota", "enabled", "type", )

    def create(self, validated_data):
        """Set permissions."""
        domain = models.Domain(**validated_data)
        domain.save(creator=self.context["request"].user)
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

    def create(self, validated_data):
        """Custom creation."""
        domain_alias = models.DomainAlias(**validated_data)
        creator = self.context["request"].user
        try:
            core_signals.can_create_object.send(
                sender=self.__class__, context=creator,
                object_type="domain_aliases")
            core_signals.can_create_object.send(
                sender=self.__class__, context=domain_alias.target,
                object_type="domain_aliases")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError({
                "domain": unicode(inst)})
        domain_alias.save(creator=creator)
        return domain_alias


class MailboxSerializer(serializers.ModelSerializer):
    """Base mailbox serializer."""

    full_address = lib_fields.DRFEmailFieldUTF8()

    class Meta:
        model = models.Mailbox
        fields = ("full_address", "use_domain_quota", "quota", )


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
            validators.validate_length(value)
            validators.complexity(value)
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

    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + (
            "password", )

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
        if request.method == "PUT":
            self.fields["password"].required = False

    def validate_password(self, value):
        """Check password constraints."""
        try:
            validators.validate_length(value)
            validators.complexity(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return value

    def validate(self, data):
        """Check constraints."""
        master_user = data.get("master_user", False)
        if master_user and data["role"] != "SuperAdmins":
            raise serializers.ValidationError({
                "master_user": _("Not allowed for this role.")
            })
        if data["role"] == "SimpleUsers":
            mailbox = data.get("mailbox")
            if mailbox is None:
                data["mailbox"] = {
                    "full_address": data["username"], "use_domain_quota": True
                }
            elif mailbox["full_address"] != data["username"]:
                raise serializers.ValidationError({
                    "username": _("Must be equal to mailbox full_address")
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
                object_type="mailboxes")
            core_signals.can_create_object.send(
                sender=self.__class__, context=domain,
                object_type="mailboxes")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError({
                "domain": unicode(inst)})
        mb = admin_models.Mailbox(
            user=account, address=address, domain=domain, **data)
        mb.set_quota(
            data.get("quota"), creator.has_perm("admin.add_domain")
        )
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
        user = core_models.User(**validated_data)
        user.set_password(validated_data["password"])
        user.save(creator=creator)
        if mailbox_data:
            self._create_mailbox(creator, user, mailbox_data)
        user.role = role
        self.set_permissions(user, domains)
        return user

    def update(self, instance, validated_data):
        """Update account and associated objects."""
        mailbox_data = validated_data.pop("mailbox")
        password = validated_data.pop("password", None)
        domains = validated_data.pop("domains", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)
        instance.save()
        if mailbox_data:
            creator = self.context["request"].user
            if instance.mailbox:
                # FIXME: compat, to remove ASAP.
                mailbox_data["email"] = mailbox_data["full_address"]
                instance.mailbox.update_from_dict(creator, mailbox_data)
            else:
                self._create_mailbox(creator, instance, mailbox_data)
        self.set_permissions(instance, domains)
        return instance


class AliasSerializer(serializers.ModelSerializer):
    """Base Alias serializer."""

    address = lib_fields.DRFEmailFieldUTF8AndEmptyUser()
    recipients = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8AndEmptyUser(),
        allow_empty=False)

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
                object_type="mailbox_aliases")
            core_signals.can_create_object.send(
                sender=self.__class__, context=self.domain,
                object_type="mailbox_aliases")
        except lib_exceptions.ModoboaException as inst:
            raise serializers.ValidationError(unicode(inst))
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
