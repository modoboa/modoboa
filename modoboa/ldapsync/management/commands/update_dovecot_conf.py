"""Command to populate local database from a remote LDAP directory."""

from django.core.management.base import BaseCommand
from django.conf import settings

from modoboa.parameters import tools as param_tools
from modoboa.admin.models import NeedDovecotUpdate

from ... import lib

class Command(BaseCommand):
    """Command definition."""

    help = "Update dovecot configuration file from modoboa LDAP parameters"

    def handle(self, *args, **options):
        """Command entry point."""
        need_dovecot_update = NeedDovecotUpdate.load()

        if need_dovecot_update.state:
            config = dict(param_tools.get_global_parameters("core"))
            if config["authentication_type"] != "ldap" or not config["ldap_dovecot_sync"]:
                return
            lib.update_dovecot_config_file(config)

            need_dovecot_update.state = False
            need_dovecot_update.save()
