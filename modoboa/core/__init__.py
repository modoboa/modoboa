
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib import parameters, events

BASE_EVENTS = [
    "CanCreate",

    "AccountCreated",
    "AccountAutoCreated",
    "AccountModified",
    "AccountDeleted",
    "AccountExported",
    "AccountImported",
    "PasswordUpdated",
    "ExtraAccountActions",
    "RoleChanged",
    "GetExtraRoles",
    "GetExtraRolePermissions",
    "PasswordChange",
    "UserCanSetRole",

    "InitialDataLoaded",

    "UserMenuDisplay",
    "AdminMenuDisplay",
    "GetStaticContent",

    "UserLogin",
    "UserLogout",

    "GetAnnouncement",

    "TopNotifications",
    "ExtraAdminContent",

    "ExtraUprefsRoutes",
    "ExtraUprefsJS",

    "GetExtraParameters",
    "ExtraFormFields",
    "SaveExtraFormFields",
]

PERMISSIONS = {
    "SimpleUsers": []
}


def load_core_settings():
    """Load core settings.

    This function must be manually called (see :file:`urls.py`) in
    order to load base settings.
    """
    from modoboa.core.app_settings import GeneralParametersForm

    parameters.register(GeneralParametersForm, ugettext_lazy("General"))
    events.declare(BASE_EVENTS)


@events.observe("TopNotifications")
def check_for_new_version(request, include_all):
    """
    Check if a new version of Modoboa is available.
    """
    from modoboa.core.utils import check_for_updates

    if not request.user.is_superuser:
        return []
    status, extensions = check_for_updates(request)
    if not status:
        return [{"id": "newversionavailable"}] if include_all else []
    return [{
        "id": "newversionavailable",
        "url": reverse("core:index") + "#info/",
        "text": _("One or more updates are available"),
        "level": "info",
    }]
