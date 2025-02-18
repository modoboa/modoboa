"""Admin API v2 serializers."""

import ipaddress
from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import validators as dj_validators
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from django.contrib.auth import password_validation
from django.contrib.auth.models import Permission

from rest_framework import serializers

from modoboa.admin import signals as admin_signals
from modoboa.admin.api.v1 import serializers as v1_serializers
from modoboa.core import models as core_models, signals as core_signals
from modoboa.lib import email_utils
from modoboa.lib import exceptions as lib_exceptions
from modoboa.lib import fields as lib_fields
from modoboa.lib import validators, web_utils
from modoboa.lib.sysutils import exec_cmd
from modoboa.parameters import tools as param_tools
from modoboa.limits import constants as limits_constants
from modoboa.limits import models as limits_models
from modoboa.transport import models as transport_models
from modoboa.transport.api.v2 import serializers as transport_serializers

from ... import constants, models


class CreateDomainAdminSerializer(serializers.Serializer):
    """Sub serializer for domain administrator creation."""

    username = serializers.CharField()
    password = serializers.CharField(required=False)
    with_mailbox = serializers.BooleanField(default=False)
    with_aliases = serializers.BooleanField(default=False)


class DomainResourceSerializer(serializers.ModelSerializer):
    """Serializer for domain resource."""

    class Meta:
        fields = ("name", "label", "max_value", "current_value", "usage")
        model = limits_models.DomainObjectLimit


class DomainSerializer(v1_serializers.DomainSerializer):
    """Domain serializer for v2 API."""

    domain_admin = CreateDomainAdminSerializer(required=False, write_only=True)
    transport = transport_serializers.TransportSerializer(required=False)

    class Meta(v1_serializers.DomainSerializer.Meta):
        fields = v1_serializers.DomainSerializer.Meta.fields + (
            "domain_admin",
            "transport",
            "opened_alarms_count",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not param_tools.get_global_parameter("enable_domain_limits", app="limits"):
            return
        self.fields["resources"] = DomainResourceSerializer(
            many=True, source="domainobjectlimit_set", required=False
        )

    def validate(self, data):
        result = super().validate(data)
        dtype = data.get("type", "domain")
        if dtype == "relaydomain" and not data.get("transport"):
            raise serializers.ValidationError(
                {"transport": _("This field is required")}
            )
        return result

    def create(self, validated_data):
        """Create administrator and other stuff if needed."""
        domain_admin = validated_data.pop("domain_admin", None)
        transport_def = validated_data.pop("transport", None)
        domain = super().create(validated_data)
        if transport_def:
            transport = transport_models.Transport(**transport_def)
            transport.pattern = domain.name
            transport.save()
            domain.transport = transport
            domain.save()

        if not domain_admin:
            return domain

        # 1. Create a domain administrator
        username = "{}@{}".format(domain_admin["username"], domain.name)
        try:
            da = core_models.User.objects.get(username=username)
        except core_models.User.DoesNotExist:
            pass
        else:
            raise lib_exceptions.Conflict(_("User '%s' already exists") % username)
        user = self.context["request"].user
        core_signals.can_create_object.send(
            self.__class__, context=user, klass=models.Mailbox
        )
        da = core_models.User(username=username, email=username, is_active=True)
        password = domain_admin.get("password")
        if password is None:
            password = param_tools.get_global_parameter("default_password", app="core")
        da.set_password(password)
        da.save()
        da.role = "DomainAdmins"
        da.post_create(user)

        # 2. Create mailbox if needed
        if domain_admin["with_mailbox"]:
            dom_admin_username = domain_admin["username"]
            mb = models.Mailbox(
                address=dom_admin_username,
                domain=domain,
                user=da,
                use_domain_quota=True,
            )
            mb.set_quota(override_rules=user.has_perm("admin.change_domain"))
            mb.save(creator=user)

            # 3. Create aliases if needed
            condition = (
                domain.type == "domain"
                and domain_admin["with_aliases"]
                and dom_admin_username != "postmaster"
            )
            if condition:
                core_signals.can_create_object.send(
                    self.__class__, context=user, klass=models.Alias
                )
                address = f"postmaster@{domain.name}"
                alias = models.Alias.objects.create(
                    address=address, domain=domain, enabled=True
                )
                alias.set_recipients([mb.full_address])
                alias.post_create(user)

        domain.add_admin(da)
        return domain

    def update(self, instance, validated_data):
        """Update domain and create/update transport."""
        transport_def = validated_data.pop("transport", None)
        resources = validated_data.pop("domainobjectlimit_set", None)
        super().update(instance, validated_data)
        if transport_def and instance.type == "relaydomain":
            transport = getattr(instance, "transport", None)
            created = False
            if transport:
                for key, value in transport_def.items():
                    setattr(instance, key, value)
                transport._settings = transport_def["_settings"]
            else:
                transport = transport_models.Transport(**transport_def)
                created = True
            transport.pattern = instance.name
            transport.save()
            if created:
                instance.transport = transport
                instance.save()
        if resources:
            for resource in resources:
                instance.domainobjectlimit_set.filter(name=resource["name"]).update(
                    max_value=resource["max_value"]
                )
        return instance


class DeleteDomainSerializer(serializers.Serializer):
    """Serializer used with delete operation."""

    keep_folder = serializers.BooleanField(default=False)


class AdminGlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # Domain settings
    enable_mx_checks = serializers.BooleanField(default=True)
    valid_mxs = serializers.CharField(allow_blank=True)
    domains_must_have_authorized_mx = serializers.BooleanField(default=False)
    enable_ipv6_mx_checks = serializers.BooleanField(default=True)
    enable_spf_checks = serializers.BooleanField(default=True)
    enable_dkim_checks = serializers.BooleanField(default=True)
    enable_dmarc_checks = serializers.BooleanField(default=True)
    enable_autoconfig_checks = serializers.BooleanField(default=True)
    custom_dns_server = serializers.IPAddressField(allow_blank=True)
    enable_dnsbl_checks = serializers.BooleanField(default=True)
    dkim_keys_storage_dir = serializers.CharField(allow_blank=True)
    dkim_default_key_length = serializers.ChoiceField(
        default=2048, choices=constants.DKIM_KEY_LENGTHS
    )
    default_domain_quota = serializers.IntegerField(default=0)
    default_domain_message_limit = serializers.IntegerField(
        required=False, allow_null=True
    )

    # Mailboxes settings
    handle_mailboxes = serializers.BooleanField(default=False)
    default_mailbox_quota = serializers.IntegerField(default=0)
    default_mailbox_message_limit = serializers.IntegerField(
        required=False, allow_null=True
    )
    auto_account_removal = serializers.BooleanField(default=False)
    auto_create_domain_and_mailbox = serializers.BooleanField(default=True)
    create_alias_on_mbox_rename = serializers.BooleanField(default=False)

    def validate_default_domain_quota(self, value):
        """Ensure quota is a positive integer."""
        if value < 0:
            raise serializers.ValidationError(_("Must be a positive integer"))
        return value

    def validate_default_mailbox_quota(self, value):
        """Ensure quota is a positive integer."""
        if value < 0:
            raise serializers.ValidationError(_("Must be a positive integer"))
        return value

    def validate_dkim_keys_storage_dir(self, value):
        """Check that directory exists."""
        if value:
            code, output = exec_cmd("which openssl")
            if code:
                raise serializers.ValidationError(
                    _("openssl not found, please make sure it is installed.")
                )
        return value

    def validate_valid_mxs(self, value):
        """Make sure it only contains IP addresses."""
        if not value:
            return value
        try:
            [ipaddress.ip_network(v.strip()) for v in value.split() if v.strip()]
        except ValueError:
            raise serializers.ValidationError(
                _("This field only allows valid IP addresses (or networks)")
            ) from None
        return value

    def validate_auto_create_domain_and_mailbox(self, value):
        """
        Make sure the option does not get deactivated
        while imap migration is enabled.
        """
        if not value and param_tools.get_global_parameter(
            "enabled_imapmigration", "imap_migration"
        ):
            raise serializers.ValidationError(
                _("Please disable imap migration before disabling this option.")
            )
        return value

    def validate(self, data):
        """Check MX options."""
        condition = (
            data.get("enable_mx_checks")
            and data.get("domains_must_have_authorized_mx")
            and not data.get("valid_mxs")
        )
        if condition:
            raise serializers.ValidationError(
                {"valid_mxs": _("Define at least one authorized network / address")}
            )
        if not data.get("enable_mx_checks"):
            data["enable_ipv6_mx_checks"] = False
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


class IdPossibleActionsSerializer(serializers.Serializer):
    """Serialiser used to get possible actions related to identities."""

    name = serializers.CharField()
    icon = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField()
    content_type = serializers.CharField(required=False)
    url = serializers.CharField(required=False)
    filename = serializers.CharField(required=False)


class IdentitySerializer(serializers.Serializer):
    """Serializer used for identities."""

    pk = serializers.IntegerField()
    type = serializers.CharField()
    identity = serializers.CharField()
    name_or_rcpt = serializers.CharField()
    tags = TagSerializer(many=True)

    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)
        self.fields["possible_actions"] = serializers.SerializerMethodField()

    def get_possible_actions(self, identity):
        if not isinstance(identity, core_models.User):
            # Return empty action list if identity type is an alias
            # (not used for now)
            return []
        actions = admin_signals.extra_account_identities_actions.send(
            self.__class__, account=identity
        )
        cleaned_actions = []
        for action in actions:
            try:
                serialized_data = IdPossibleActionsSerializer(action[1]).data
                cleaned_actions.append(serialized_data)
            except (ValidationError, AttributeError):
                continue
        return cleaned_actions


class AccountResourceSerializer(serializers.ModelSerializer):
    """Serializer for user resource."""

    class Meta:
        fields = ("name", "label", "max_value", "current_value", "usage")
        model = limits_models.UserObjectLimit


class AccountMeSerializer(v1_serializers.AccountSerializer):
    """Custom Account serializer for connected user."""

    permissions = serializers.SerializerMethodField()

    class Meta(v1_serializers.AccountSerializer.Meta):
        fields = v1_serializers.AccountSerializer.Meta.fields + ("permissions",)

    def get_permissions(self, user) -> List[str]:
        """Return available permissions for given user."""
        permissions = (
            user.user_permissions.all() | Permission.objects.filter(group__user=user)
        ).select_related("content_type")
        return [f"{p.content_type.app_label}.{p.codename}" for p in permissions]


class AccountSerializer(v1_serializers.AccountSerializer):
    """Add support for user resources."""

    aliases = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8(), source="mailbox.alias_addresses"
    )

    class Meta(v1_serializers.AccountSerializer.Meta):
        fields = v1_serializers.AccountSerializer.Meta.fields + ("aliases",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not param_tools.get_global_parameter("enable_admin_limits", app="limits"):
            return
        self.fields["resources"] = serializers.SerializerMethodField()

    def get_resources(self, account) -> List[AccountResourceSerializer]:
        if account.role == "SimpleUsers":
            return []
        resources = []
        for limit in account.userobjectlimit_set.all():
            tpl = limits_constants.DEFAULT_USER_LIMITS[limit.name]
            if "required_role" in tpl:
                if account.role != tpl["required_role"]:
                    continue
            resources.append(limit)
        return AccountResourceSerializer(resources, many=True).data


class MailboxSerializer(serializers.ModelSerializer):
    """Base mailbox serializer."""

    quota = serializers.CharField(required=False)

    class Meta:
        model = models.Mailbox
        fields = (
            "pk",
            "use_domain_quota",
            "quota",
            "message_limit",
            "is_send_only",
        )

    def validate_quota(self, value):
        """Convert quota to MB."""
        return web_utils.size2integer(value, output_unit="MB")

    def validate(self, data):
        """Check if quota is required."""
        method = self.context["request"].method
        if not data.get("use_domain_quota", False):
            if "quota" not in data and method != "PATCH":
                raise serializers.ValidationError(
                    {"quota": _("This field is required")}
                )
        return data


class WritableResourceSerializer(serializers.ModelSerializer):
    """Serializer used to update resource."""

    class Meta:
        fields = ("name", "max_value")
        model = limits_models.UserObjectLimit


class WritableAccountSerializer(v1_serializers.WritableAccountSerializer):
    """Add support for aliases and sender addresses."""

    aliases = serializers.ListField(
        child=lib_fields.DRFEmailFieldUTF8(), required=False
    )
    mailbox = MailboxSerializer(required=False)

    class Meta(v1_serializers.WritableAccountSerializer.Meta):
        fields = tuple(
            field
            for field in v1_serializers.WritableAccountSerializer.Meta.fields
            if field != "random_password"
        ) + ("aliases",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not param_tools.get_global_parameter("enable_admin_limits", app="limits"):
            return
        self.fields["resources"] = WritableResourceSerializer(many=True, required=False)

    def validate_aliases(self, value):
        """Check if required domains are locals and user can access them."""
        aliases = []
        for alias in value:
            localpart, domain = models.validate_alias_address(
                alias, self.context["request"].user, ignore_existing=True
            )
            aliases.append({"localpart": localpart, "domain": domain})
        return aliases

    def validate(self, data):
        """Check constraints."""
        master_user = data.get("master_user", False)
        role = data.get("role")
        if master_user and role != "SuperAdmins":
            raise serializers.ValidationError(
                {"master_user": _("Not allowed for this role.")}
            )
        if role == "SimpleUsers":
            username = data.get("username")
            if username:
                try:
                    validators.UTF8EmailValidator()(username)
                except ValidationError as err:
                    raise ValidationError({"username": err.message}) from None
            mailbox = data.get("mailbox")
            if mailbox is None:
                if not self.instance:
                    data["mailbox"] = {"use_domain_quota": True}
        if "mailbox" in data and "username" in data:
            self.address, domain_name = email_utils.split_mailbox(data["username"])
            self.domain = get_object_or_404(models.Domain, name=domain_name)
            creator = self.context["request"].user
            if not creator.can_access(self.domain):
                raise serializers.ValidationError({"mailbox": _("Permission denied.")})
            if not self.instance:
                try:
                    core_signals.can_create_object.send(
                        sender=self.__class__, context=creator, klass=models.Mailbox
                    )
                    core_signals.can_create_object.send(
                        sender=self.__class__,
                        context=self.domain,
                        object_type="mailboxes",
                    )
                except lib_exceptions.ModoboaException as inst:
                    raise serializers.ValidationError({"mailbox": str(inst)}) from None
            if len(self.address) > 64:
                raise serializers.ValidationError(
                    {
                        "username": _(
                            "The left part of an email address can't be more than 64 characters."
                        )
                    }
                )
        if data.get("password") or not self.partial:
            password = data.get("password")
            if password:
                try:
                    password_validation.validate_password(
                        data["password"], self.instance
                    )
                except ValidationError as exc:
                    raise serializers.ValidationError(
                        {"password": exc.messages[0]}
                    ) from None
            elif not self.instance:
                raise serializers.ValidationError(
                    {"password": _("This field is required.")}
                )
        aliases = data.get("aliases")
        if aliases and "mailbox" not in data:
            raise serializers.ValidationError(
                {"aliases": _("A mailbox is required to create aliases.")}
            )
        domain_names = data.get("domains")
        if not domain_names:
            return data
        domains = []
        for name in domain_names:
            domain = models.Domain.objects.filter(name=name).first()
            if domain:
                domains.append(domain)
                continue
            raise serializers.ValidationError(
                {"domains": _("Local domain {} does not exist").format(name)}
            )
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
                models.Alias.objects.modify_or_create(
                    address="{}@{}".format(alias["localpart"], alias["domain"]),
                    recipients=[user.username],
                    creator=creator,
                    domain=alias["domain"],
                )
        return user

    def update(self, instance, validated_data):
        """Update account and associated objects."""
        mailbox_data = validated_data.pop("mailbox", None)
        password = validated_data.pop("password", None)
        domains = validated_data.pop("domains", [])
        aliases = validated_data.pop("aliases", None)
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
        if aliases is not None and "username" in validated_data:
            # We create a list to keep track of alias we need to delete
            alias_recipients = instance.mailbox.alias_addresses
            for alias in aliases:
                address = "{}@{}".format(alias["localpart"], alias["domain"])
                models.Alias.objects.modify_or_create(
                    address=address,
                    recipients=[validated_data["username"]],
                    creator=creator,
                    domain=alias["domain"],
                )
                try:
                    alias_recipients.remove(address)
                except ValueError:
                    continue
            for alias_address in alias_recipients:
                alias = models.Alias.objects.filter(
                    address=alias_address, internal=False
                )
                if alias.exists():
                    alias.first().remove_recipient_or_delete(validated_data["username"])
        instance.save()
        resources = validated_data.get("resources")
        if resources:
            for resource in resources:
                instance.userobjectlimit_set.filter(name=resource["name"]).update(
                    max_value=resource["max_value"]
                )
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
        ) + ("expire_at", "description", "creation", "last_modification")


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


class CSVImportSerializer(serializers.Serializer):
    """Base serializer for all CSV import endpoints."""

    sourcefile = serializers.FileField()
    sepchar = serializers.CharField(required=False, default=";")
    continue_if_exists = serializers.BooleanField(default=False)


class CSVIdentityImportSerializer(CSVImportSerializer):
    """Custom serializer for identity import."""

    crypt_password = serializers.BooleanField()


class AlarmSerializer(serializers.ModelSerializer):
    """Serializer for Alarm related endpoints."""

    class Meta:
        depth = 1
        fields = "__all__"
        model = models.Alarm


class AlarmSwitchStatusSerializer(serializers.Serializer):
    """Serializer to switch the status of an Alarm."""

    status = serializers.IntegerField()

    def validate(self, data):
        if data["status"] not in [constants.ALARM_OPENED, constants.ALARM_CLOSED]:
            raise ValidationError(_("Unknown status"))
        return data
