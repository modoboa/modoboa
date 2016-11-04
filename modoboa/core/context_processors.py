"""Custom context processors."""

from modoboa.lib import events


def top_notifications(request):
    """A context processor to include top notifications."""
    if request.user.is_anonymous():
        return {}
    interval = request.localconfig.parameters.get_value(
        "top_notifications_check_interval")
    return {
        "notifications_check_interval": interval * 1000,
        "top_notifications": events.raiseQueryEvent(
            "TopNotifications", request, False)
    }
