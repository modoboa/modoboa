"""API v2 serializers."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from modoboa.admin.models import Mailbox
from modoboa.admin.models.domain import Domain

from modoboa.imap_migration import models


class IMAPMigrationSettingsSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    # General
    enabled_imapmigration = serializers.BooleanField(default=True)

    # OfflineIMAP settings
    max_sync_accounts = serializers.IntegerField(default=1)

    # OfflineIMAP Filter settings
    create_folders = serializers.BooleanField(default=True)
    folder_filter_exclude = serializers.CharField(
        required=False, allow_blank=True, default=""
    )
    folder_filter_include = serializers.CharField(
        required=False, allow_blank=True, default=""
    )


class EmailProviderDomainSerializer(serializers.ModelSerializer):
    """Serializer class for EmailProviderDomain."""

    id = serializers.IntegerField(required=False)

    class Meta:
        extra_kwargs = {"name": {"validators": []}}
        fields = ("id", "name", "new_domain")
        model = models.EmailProviderDomain


class EmailProviderSerializer(serializers.ModelSerializer):
    """Serializer class for EmailProvider."""

    domains = EmailProviderDomainSerializer(many=True, required=False)

    class Meta:
        fields = "__all__"
        model = models.EmailProvider

    def create(self, validated_data):
        """Create provider and domains."""
        domains = validated_data.pop("domains", None)
        validated_data.pop("id", None)
        provider = models.EmailProvider.objects.create(**validated_data)
        if domains:
            to_create = []
            for domain in domains:
                to_create.append(
                    models.EmailProviderDomain(provider=provider, **domain)
                )
            models.EmailProviderDomain.objects.bulk_create(to_create)
        return provider

    def update(self, instance, validated_data):
        """Update provider and domains."""
        domains = validated_data.pop("domains", [])
        domain_ids = [domain["id"] for domain in domains if "id" in domain]
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        for domain in instance.domains.all():
            if domain.id not in domain_ids:
                domain.delete()
            else:
                for updated_domain in domains:
                    if updated_domain.get("id") != domain.id:
                        continue
                    domain.name = updated_domain["name"]
                    domain.new_domain = updated_domain.get("new_domain")
                    domain.save()
                    domains.remove(updated_domain)
                    break
        to_create = []
        for new_domain in domains:
            to_create.append(
                models.EmailProviderDomain(
                    name=new_domain["name"],
                    new_domain=new_domain.get("new_domain"),
                    provider=instance,
                )
            )
        models.EmailProviderDomain.objects.bulk_create(to_create)
        return instance


class CheckProviderSerializer(serializers.Serializer):
    """A serializer for checking connection to IMAP server."""

    address = serializers.CharField()
    port = serializers.IntegerField(min_value=0, max_value=65535)
    secured = serializers.BooleanField()


class CheckAssociatedDomainSerializer(serializers.Serializer):
    """A serializer for checking associated domains."""

    name = serializers.CharField()
    new_domain = serializers.PrimaryKeyRelatedField(read_only=True, required=False)

    def validate_new_domain(self, value):
        domain_ids = Domain.objects.get_for_admin(
            self.context["request"].user
        ).values_list("id", flat=True)
        if value not in domain_ids:
            raise serializers.ValidationError(_("Access denied"))
        return value


class MailboxSerializer(serializers.ModelSerializer):
    """Simple mailbox serializer."""

    class Meta:
        fields = ("id", "full_address", "user")
        model = Mailbox


class MigrationSerializer(serializers.ModelSerializer):
    """Serializer class for Migration."""

    mailbox = MailboxSerializer()

    class Meta:
        depth = 1
        fields = ("id", "provider", "mailbox", "username")
        model = models.Migration
