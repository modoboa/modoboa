"""Command to populate local database from a remote LDAP directory."""

from django.core.management.base import BaseCommand
from django.conf import settings

from modoboa.parameters import tools as param_tools

from ... import lib
from modoboa.core import models

class Command(BaseCommand):
    """Command definition."""

    help = "Update dovecot configuration file from modoboa LDAP parameters"

    def handle(self, *args, **options):
        """Command entry point."""
        localconfig = models.LocalConfig.objects.first()

        if localconfig.need_dovecot_update:
            config = dict(param_tools.get_global_parameters("core"))
            if config["authentication_type"] == "ldap" and config["ldap_dovecot_sync"]:
                lib.update_dovecot_config_file(config)
            localconfig.need_dovecot_update = False
            localconfig.save()
