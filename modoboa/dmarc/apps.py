"""AppConfig for dmarc."""

from django.apps import AppConfig

from modoboa.dmarc.forms import load_settings


class DmarcConfig(AppConfig):
    """App configuration."""

    name = "modoboa.dmarc"
    verbose_name = "Modoboa DMARC tools"

    def ready(self):
        load_settings()
        from . import handlers  # noqa
