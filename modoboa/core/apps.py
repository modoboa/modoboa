"""Core config for admin."""

from django.apps import AppConfig
from django.db.models import signals


BASE_EVENTS = [
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


def load_core_settings():
    """Load core settings.

    This function must be manually called (see :file:`urls.py`) in
    order to load base settings.
    """
    from django.utils.translation import ugettext_lazy
    from modoboa.lib import parameters, events
    from .app_settings import GeneralParametersForm

    parameters.register(GeneralParametersForm, ugettext_lazy("General"))
    events.declare(BASE_EVENTS)


class CoreConfig(AppConfig):

    """App configuration."""

    name = "modoboa.core"
    verbose_name = "Modoboa core"

    def ready(self):
        load_core_settings()

        from . import handlers

        signals.post_migrate.connect(handlers.create_local_config, sender=self)
