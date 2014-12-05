"""
Custom context processors.
"""
from modoboa.lib import events, parameters


def top_notifications(request):
    """
    A context processor to include top notifications.
    """
    if request.user.is_anonymous():
        return {}
    return {
        "notifications_check_interval":
        int(parameters.get_admin("TOP_NOTIFICATIONS_CHECK_INTERVAL")) * 1000,
        "top_notifications": events.raiseQueryEvent(
            "TopNotifications", request, False)
    }
