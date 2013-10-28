from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters, events

base_events = [
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
    "PasswordChange",
    "UserCanSetRole",

    "UserMenuDisplay",
    "AdminMenuDisplay",
    "GetStaticContent",

    "ExtEnabled",
    "ExtDisabled",

    "UserLogin",
    "UserLogout",

    "GetAnnouncement",

    "TopNotifications",
    "ExtraAdminContent",

    "ExtraUprefsRoutes",
    "ExtraUprefsJS",

    "GetExtraParameters"
]


def load_settings():
    from .app_settings import GeneralParametersForm, UserSettings

    parameters.register(GeneralParametersForm, ugettext_lazy("General"))
    parameters.register(UserSettings, ugettext_lazy("General"))
    events.declare(base_events)


@events.observe("ExtDisabled")
def unset_default_topredirection(extension):
    """
    Simple callback to change the default redirection if the
    corresponding extension is being disabled.
    """
    topredirection = parameters.get_admin("DEFAULT_TOP_REDIRECTION")
    if topredirection == extension.name:
        parameters.save_admin("DEFAULT_TOP_REDIRECTION", "userprefs")
