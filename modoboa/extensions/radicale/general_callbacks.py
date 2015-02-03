"""
General callbacks.
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events

PERMISSIONS = [
    ("radicale", "usercalendar", "add_usercalendar"),
    ("radicale", "usercalendar", "change_usercalendar"),
    ("radicale", "usercalendar", "delete_usercalendar"),
    ("radicale", "sharedcalendar", "add_sharedcalendar"),
    ("radicale", "sharedcalendar", "change_sharedcalendar"),
    ("radicale", "sharedcalendar", "delete_sharedcalendar")
]

ROLES_PERMISSIONS = {
    "DomainAdmins": PERMISSIONS,
    "Resellers": PERMISSIONS
}


@events.observe("GetExtraRolePermissions")
def extra_permissions(rolename):
    """Extra permissions."""
    return ROLES_PERMISSIONS.get(rolename, [])


@events.observe("UserMenuDisplay")
def top_menu(target, user):
    if target == "top_menu":
        return [
            {"name": "radicale",
             "label": _("Calendars"),
             "url": reverse('radicale:index')}
        ]
    return []
