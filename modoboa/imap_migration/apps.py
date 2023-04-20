"""AppConfig for IMAP migration."""

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


def load_imapmigration_settings():
    """Load core settings.

    This function must be manually called (see :file:`urls.py`) in
    order to load base settings.
    """
    from modoboa.parameters import tools as param_tools
    from . import app_settings
    from .api.v2 import serializers

    param_tools.registry.add(
        "global", app_settings.ParametersForm, ugettext_lazy("IMAP Migration"))
    param_tools.registry.add2(
        "global", "imap_migration", ugettext_lazy("IMAP Migration"),
        app_settings.IMAP_MIGRATION_PARAMETERS_STRUCT,
        serializers.IMAPMigrationSettingsSerializer,
        True)


class IMAPMigrationConfig(AppConfig):
    """App configuration."""

    name = "modoboa.imap_migration"
    verbose_name = "Migration through IMAP for Modoboa"

    def ready(self):
        from . import checks  # noqa

        load_imapmigration_settings()
