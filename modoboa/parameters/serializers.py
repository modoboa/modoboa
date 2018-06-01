"""Parameters serializers."""

from rest_framework import serializers

from . import tools


class ParametersSerializer(serializers.Serializer):
    """Parameters serializer."""

    def __init__(self, *args, **kwargs):
        """Generate serializer."""
        super(ParametersSerializer, self).__init__(*args, **kwargs)
        for name, field in tools.registry.get_fields("global"):
            field.source = None
            self.fields[name] = field
