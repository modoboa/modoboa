"""Admin serializers."""

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from rest_framework import serializers
from passwords import validators

from modoboa.admin import models as admin_models
from modoboa.core import models as core_models
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

    class Meta:
        model = core_models.User
        fields = (
            "pk", "username", "first_name", "last_name", "is_active",
            "master_user", "mailbox", "role", "language", "phone_number",
            "secondary_email",
        )

    def __init__(self, *args, **kwargs):
        """Adapt fields to current user."""
        super(AccountSerializer, self).__init__(*args, **kwargs)
        user = self.context["request"].user
        if not user.is_superuser:
            del self.fields["master_user"]

    def get_role(self, account):
        """Return role."""
        return account.group


class AccountExistsSerializer(serializers.Serializer):
    """Simple serializer used with existence checks."""

    exists = serializers.BooleanField()


class WritableAccountSerializer(AccountSerializer):
    """Serializer to create account."""

    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + (
            "password", )

    def __init__(self, *args, **kwargs):
        """Adapt fields to current user."""
        super(WritableAccountSerializer, self).__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["role"] = serializers.ChoiceField(
            choices=permissions.get_account_roles(user))

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
        mb = admin_models.Mailbox(
            user=account, address=address, domain=domain, **data)
        mb.set_quota(
            data.get("quota"), creator.has_perm("admin.add_domain")
        )
        mb.save(creator=creator)
        account.email = full_address
        return mb

    def create(self, validated_data):
        """Create appropriate objects."""
        creator = self.context["request"].user
        mailbox_data = validated_data.pop("mailbox", None)
        role = validated_data.pop("role")
        user = core_models.User(**validated_data)
        user.set_password(validated_data["password"])
        user.save(creator=creator)
        if mailbox_data:
            self._create_mailbox(creator, user, mailbox_data)
        user.role = role
        return user

    def update(self, instance, validated_data):
        """Update account and associated objects."""
        mailbox_data = validated_data.pop("mailbox")
        password = validated_data.pop("password")
        for key, value in validated_data.items():
            setattr(instance, key, value)
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
        return instance
