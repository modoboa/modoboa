"""Custom context processors."""

from functools import reduce
from django.conf import settings

from . import signals


def top_notifications(request):
    """A context processor to include top notifications."""
    if request.user.is_anonymous:
        return {}
    interval = request.localconfig.parameters.get_value(
        "top_notifications_check_interval"
    )
    notifications = signals.get_top_notifications.send(
        sender="top_notifications", include_all=False
    )
    notifications = reduce(lambda a, b: a + b, [notif[1] for notif in notifications])
    return {
        "notifications_check_interval": interval * 1000,
        "top_notifications": notifications,
    }


def new_admin_url(*args):
    """A context processor to include new admin url."""
    return {"new_admin": getattr(settings, "NEW_ADMIN_URL", "new-admin")}
