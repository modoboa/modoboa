"""IMAP migration handlers."""

from django.urls import reverse
from django.dispatch import receiver
from django.utils.translation import ugettext as _

from modoboa.core import signals as core_signals


@receiver(core_signals.extra_user_menu_entries)
def menu(sender, location, user, **kwargs):
    """Return extra menu entry."""
    if location != "top_menu" or not user.is_superuser:
        return []
    return [
        {"name": "imap_migrations",
         "label": _("IMAP migrations"),
         "url": reverse("imap_migration:index")}
    ]
