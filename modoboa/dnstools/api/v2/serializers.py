"""App related serializers."""

from rest_framework import serializers

from modoboa.admin import models as admin_models

from ... import models


class MXRecordSerializer(serializers.ModelSerializer):
    """Serializer for MXRecord."""

    class Meta:
        model = admin_models.MXRecord
        fields = ("name", "address", "updated")


class DNSBLResultSerializer(serializers.ModelSerializer):
    """Serializer for DNSBLResult."""

    mx = MXRecordSerializer()

    class Meta:
        model = admin_models.DNSBLResult
        fields = ("provider", "mx", "status")


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
    dnsbl_results = DNSBLResultSerializer(many=True, source="dnsblresult_set")

    class Meta:
        model = admin_models.Domain
        fields = (
            "mx_records",
            "dnsbl_results",
            "autoconfig_record",
            "autodiscover_record",
            "spf_record",
            "dkim_record",
            "dmarc_record",
        )
