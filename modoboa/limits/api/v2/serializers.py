"""Limits serializers for API v2."""

from rest_framework import serializers


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
