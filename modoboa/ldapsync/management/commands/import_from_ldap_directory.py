"""Command to populate local database from a remote LDAP directory."""

from django.core.management.base import BaseCommand

from modoboa.parameters import tools as param_tools

from ... import lib


class Command(BaseCommand):
    """Command definition."""

    help = "Populate database from remote LDAP directory"

    def handle(self, *args, **options):
        """Command entry point."""
        config = dict(param_tools.get_global_parameters("core"))
        if not config["ldap_enable_import"]:
            return
        lib.import_accounts_from_ldap(config)
