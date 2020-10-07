"""Limits serializers."""

from rest_framework import serializers

from . import lib


class ResourcesSerializer(serializers.Serializer):
    """Resources serializer."""

    domains = serializers.IntegerField(min_value=-1)
    domain_aliases = serializers.IntegerField(min_value=-1)
    mailboxes = serializers.IntegerField(min_value=-1)
    mailbox_aliases = serializers.IntegerField(min_value=-1)
    domain_admins = serializers.IntegerField(min_value=-1)
    quota = serializers.IntegerField(min_value=0)

    def to_representation(self, instance):
        """Return limits."""
        return [
            (limit.name, limit.max_value)
            for limit in instance.userobjectlimit_set.all()
        ]

    def update(self, instance, validated_data):
        """Update limits."""
        user = self.context["request"].user
        for name, max_value in list(validated_data.items()):
            limit = instance.userobjectlimit_set.get(name=name)
            if not user.is_superuser:
                lib.allocate_resources_from_user(limit, user, max_value)
            limit.max_value = max_value
            limit.save(update_fields=["max_value"])
        return instance


class LimitsGlobalParemetersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # Per-admin limits
    enable_admin_limits = serializers.BooleanField(default=True)
    deflt_user_domain_admins_limit = serializers.IntegerField(default=0)
    deflt_user_domains_limit = serializers.IntegerField(default=0)
    deflt_user_domain_aliases_limit = serializers.IntegerField(default=0)
    deflt_user_mailboxes_limit = serializers.IntegerField(default=0)
    deflt_user_mailbox_aliases_limit = serializers.IntegerField(default=0)
    deflt_user_quota_limit = serializers.IntegerField(default=0)

    # Per-domain limits
    enable_domain_limits = serializers.BooleanField(default=False)
    deflt_domain_domain_admins_limit = serializers.IntegerField(default=0)
    deflt_domain_domain_aliases_limit = serializers.IntegerField(default=0)
    deflt_domain_mailboxes_limit = serializers.IntegerField(default=0)
    deflt_domain_mailbox_aliases_limit = serializers.IntegerField(default=0)
