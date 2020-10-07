"""Command to overwrite dovecot LDAP configuration (auth)."""

from django.core.management.base import BaseCommand

from modoboa.parameters import tools as param_tools

from ... import lib
from modoboa.core import models


class Command(BaseCommand):
    """Command definition."""

    help = "Update dovecot configuration file to enable LDAP auth"

    def handle(self, *args, **options):
        """Command entry point."""
        localconfig = models.LocalConfig.objects.first()
        if not localconfig.need_dovecot_update:
            return
        config = dict(param_tools.get_global_parameters("core"))
        condition = (
            config["authentication_type"] == "ldap" and
            config["ldap_dovecot_sync"]
        )
        if condition:
            lib.update_dovecot_config_file(config)
        localconfig.need_dovecot_update = False
        localconfig.save(update_fields=["need_dovecot_update"])
