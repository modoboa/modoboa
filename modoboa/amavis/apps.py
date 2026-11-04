"""AppConfig for amavis."""

from django.apps import AppConfig


class AmavisConfig(AppConfig):
    """App configuration."""

    name = "modoboa.amavis"
    verbose_name = "Modoboa amavis frontend"

    def ready(self):
        # Import these to force registration of checks and signals
        from . import checks  # NOQA:F401
        from . import handlers  # NOQA:F401
        from modoboa.amavis.app_settings import load_settings

        load_settings()

        from django.utils.translation import gettext_lazy
        from modoboa.core.loggers import register_audit_action

        for code, label in (
            (
                "amavis.quarantine.released",
                gettext_lazy("Quarantined messages released"),
            ),
            (
                "amavis.quarantine.release_requested",
                gettext_lazy("Quarantined messages release requested"),
            ),
            ("amavis.quarantine.deleted", gettext_lazy("Quarantined messages deleted")),
            ("amavis.quarantine.marked", gettext_lazy("Quarantined messages marked")),
        ):
            register_audit_action(code, label)
