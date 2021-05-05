"""Admin API v2 serializers."""

from django.utils.translation import ugettext as _

from rest_framework import serializers

from modoboa.admin.api.v1 import serializers as v1_serializers
from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib import fields as lib_fields
from modoboa.parameters import tools as param_tools

from ... import constants, lib, models


class CreateDomainAdminSerializer(serializers.Serializer):
    """Sub serializer for domain administrator creation."""

    username = serializers.CharField()
    with_random_password = serializers.BooleanField(default=False)
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
        if domain_admin["with_random_password"]:
            password = lib.make_password()
        else:
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
    enable_dnsbl_checks = serializers.BooleanField(default=True)
    dkim_keys_storage_dir = serializers.CharField(allow_blank=True)
    dkim_default_key_length = serializers.ChoiceField(
        default=2048, choices=constants.DKIM_KEY_LENGTHS)

    # Mailboxes settings
    handle_mailboxes = serializers.BooleanField(default=False)
    default_domain_quota = serializers.IntegerField(default=0)
    default_mailbox_quota = serializers.IntegerField(default=0)
    auto_account_removal = serializers.BooleanField(default=False)
    auto_create_domain_and_mailbox = serializers.BooleanField(default=True)
    create_alias_on_mbox_rename = serializers.BooleanField(default=False)


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
    identity = serializers.CharField()
    name_or_rcpt = serializers.CharField()
    tags = TagSerializer(many=True)


class WritableAccountSerializer(v1_serializers.WritableAccountSerializer):
    """Add support for aliases and sender addresses."""

    aliases = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8(),
        required=False
    )

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

    def create(self, validated_data):
        """Handle aliases."""
        user = self.context["request"].user
        aliases = validated_data.pop("aliases", None)
        user = super().create(validated_data)
        if aliases:
            for alias in aliases:
                models.Alias.objects.create(
                    creator=user,
                    domain=alias.domain,
                    address=alias.localpart,
                    recipients=[validated_data["mailbox"]["full_address"]]
                )
        return user


class AliasSerializer(v1_serializers.AliasSerializer):
    """Alias serializer for v2 API."""

    class Meta(v1_serializers.AliasSerializer.Meta):
        # We remove 'internal' field
        fields = ("pk", "address", "enabled", "internal", "recipients")
