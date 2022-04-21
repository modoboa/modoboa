"""ViewSet related mixins and tools."""

from reversion.views import RevisionMixin


class RevisionModelMixin(RevisionMixin):
    """
    A mixin to wrap every request in a revision block.
    """

    pass
