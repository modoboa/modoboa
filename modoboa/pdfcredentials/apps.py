"""AppConfig for PDF credentials."""

from django.apps import AppConfig

from django.utils.translation import gettext_lazy


def load_pdfcredential_settings():
    """Load core settings.

    This function must be manually called (see :file:`urls.py`) in
    order to load base settings.
    """
    from modoboa.parameters import tools as param_tools
    from . import app_settings
    from .api.v2 import serializers

    param_tools.registry.add(
        "global", app_settings.ParametersForm, gettext_lazy("PDF credentials")
    )
    param_tools.registry.add2(
        "global",
        "pdfcredentials",
        gettext_lazy("PDF Credentials"),
        app_settings.PDF_CREDENTIALS_PARAMETERS_STRUCT,
        serializers.PDFCredentialsSettingsSerializer,
        True,
    )


class PDFCredentialsConfig(AppConfig):
    """App configuration."""

    name = "modoboa.pdfcredentials"
    verbose_name = "PDF credentials for Modoboa"

    def ready(self):
        from . import handlers  # noqa

        load_pdfcredential_settings()
