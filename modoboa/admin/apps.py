"""AppConfig for admin."""

from django.apps import AppConfig

from .app_settings import load_admin_settings


class AdminConfig(AppConfig):
    """App configuration."""

    name = "modoboa.admin"
    verbose_name = "Modoboa admin console"

    def ready(self):
        load_admin_settings()

        from . import checks, handlers  # NOQA:F401

        from django.utils.translation import gettext_lazy
        from modoboa.core.loggers import register_audit_action

        register_audit_action(
            "admin.domain.admin_added", gettext_lazy("Domain administrator added")
        )
        register_audit_action(
            "admin.domain.admin_removed", gettext_lazy("Domain administrator removed")
        )
        register_audit_action(
            "admin.domain.dkim_key_generated", gettext_lazy("DKIM key generation")
        )
