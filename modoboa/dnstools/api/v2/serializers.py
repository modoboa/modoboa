"""App related serializers."""

from rest_framework import serializers

from modoboa.admin import models as admin_models

from ... import models


class DNSBLResultSerializer(serializers.ModelSerializer):
    """Serializer for DNSBLResult."""

    class Meta:
        model = admin_models.DNSBLResult
        fields = ("provider", "status")


class MXRecordSerializer(serializers.ModelSerializer):
    """Serializer for MXRecord."""

    dnsbl_results = DNSBLResultSerializer(many=True, source="active_dnsbl_results")

    class Meta:
        model = admin_models.MXRecord
        fields = ("name", "address", "dnsbl_results", "updated")


class DNSRecordSerializer(serializers.ModelSerializer):
    """Serializer for DNSRecord."""

    class Meta:
        model = models.DNSRecord
        fields = ("type", "value", "is_valid", "error", "updated")


class DNSDetailSerializer(serializers.ModelSerializer):

    mx_records = MXRecordSerializer(many=True, source="mxrecord_set")
    autoconfig_record = DNSRecordSerializer()
    autodiscover_record = DNSRecordSerializer()
    spf_record = DNSRecordSerializer()
    dkim_record = DNSRecordSerializer()
    dmarc_record = DNSRecordSerializer()

    class Meta:
        model = admin_models.Domain
        fields = (
            "mx_records",
            "autoconfig_record",
            "autodiscover_record",
            "spf_record",
            "dkim_record",
            "dmarc_record",
        )
