"""Modoboa sievefilters handlers."""

from django.urls import reverse
from django.dispatch import receiver
from django.utils.translation import gettext as _

from modoboa.core import signals as core_signals

from . import lib


@receiver(core_signals.extra_user_menu_entries)
def menu(sender, location, user, **kwargs):
    """Return extra menu entry."""
    if location != "options_menu" or not hasattr(user, "mailbox"):
        return []
    return [
        {
            "name": "sievefilters",
            "label": _("Message filters"),
            "url": reverse("sievefilters:index"),
            "img": "fa fa-filter",
        }
    ]


@receiver(core_signals.user_logout)
def userlogout(sender, request, **kwargs):
    """Close managesieve connection."""
    if not hasattr(request.user, "mailbox"):
        return
    try:
        sc = lib.SieveClient(
            user=request.user.username, password=request.session["password"]
        )
    except Exception:
        pass
    else:
        sc.logout()
