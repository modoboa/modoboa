"""App related serializers."""

from rest_framework import serializers


class TestResultSerializer(serializers.Serializer):

    success = serializers.IntegerField()
    failure = serializers.IntegerField()


class SourceSerializer(serializers.Serializer):

    total = serializers.IntegerField()
    spf = TestResultSerializer()
    dkim = TestResultSerializer()


class DMARCAligmentSerializer(serializers.Serializer):

    aligned = serializers.DictField(
        child=serializers.DictField(child=SourceSerializer())
    )
    trusted = serializers.DictField(
        child=serializers.DictField(child=SourceSerializer())
    )
    forwarded = serializers.DictField(
        child=serializers.DictField(child=SourceSerializer())
    )
    failed = serializers.DictField(
        child=serializers.DictField(child=SourceSerializer())
    )


class DmarcGlobalParametersSerializer(serializers.Serializer):
    """Serializer for global parameters."""

    enable_rlookups = serializers.BooleanField(default=False)
