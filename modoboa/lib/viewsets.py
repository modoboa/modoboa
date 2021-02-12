"""ViewSet related mixins and tools."""

from rest_framework import viewsets
from reversion.views import RevisionMixin


class ExpandableSerializerMixin:
    """
    A mixin to allow serializers with expanded fields by default.

    Useful for create/update operations that return a different output.
    """

    serializer_expanded_fields = []

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        if self.request.version == 'v2':
            kwargs['expand'] = self.serializer_expanded_fields
        return serializer_class(*args, **kwargs)


class ExpandableModelViewSet(ExpandableSerializerMixin,
                             viewsets.ModelViewSet):
    """
    A ModelViewSet version which provides an expanded serializer
    output for create/update actions.
    """

    pass


class RevisionModelMixin(RevisionMixin):
    """
    A mixin to wrap every request in a revision block.
    """

    pass
