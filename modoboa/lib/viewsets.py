"""ViewSet related mixins and tools."""

from rest_framework import permissions
from reversion.views import RevisionMixin


class RevisionModelMixin(RevisionMixin):
    """
    A mixin to wrap every request in a revision block.
    """

    pass


class HasMailbox(permissions.BasePermission):
    """Require user to has a mailbox."""

    message = "User has no mailbox."

    def has_permission(self, request, view):
        return hasattr(request.user, "mailbox")
