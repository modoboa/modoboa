"""Command to populate local database from a remote LDAP directory."""

from django.core.management.base import BaseCommand

from modoboa.parameters import tools as param_tools

from ... import lib

class Command(BaseCommand):
    """Command definition."""

    help = "Update dovecot configuration file from modoboa LDAP parameters"

    def handle(self, *args, **options):
        """Command entry point."""
        config = dict(param_tools.get_global_parameters("core"))
        if config["authentication_type"] != "ldap" or not config["ldap_dovecot_sync"]:
            return
        lib.update_dovecot_config_file(config)
