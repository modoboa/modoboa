"""A management command to create an offlineimap configuration file."""

import os
import stat

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from modoboa.admin.app_settings import load_admin_settings
from modoboa.parameters import tools as param_tools

from ...models import Migration


class Command(BaseCommand):
    """Command definition."""

    help = "Generate an offlineimap configuration file."

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--output",
            default="/tmp/offlineimap.conf",
            help="Path of the generated file",
        )
        parser.add_argument(
            "--no-restrict",
            dest="restrict",
            action="store_false",
            help="Do not restrict file permissions on generated OfflineIMAP configuration file",
        )

    def handle(self, *args, **options):
        """Entry point."""
        load_admin_settings()
        conf = dict(param_tools.get_global_parameters("imap_migration"))
        context = {
            "imap_create_folders": conf["create_folders"],
            "imap_folder_filter_exclude": conf["folder_filter_exclude"],
            "imap_folder_filter_include": ", ".join(
                f"'{w}'" for w in conf["folder_filter_include"].split(",")
            ),
            "migrations": Migration.objects.select_related(
                "provider", "mailbox__domain"
            ),
        }
        opener = None  # Default creates files using mode 0o666 (umask’d)
        if options["restrict"]:
            opener = lambda path, flags: \
                os.open(path, flags, mode=(stat.S_IRUSR | stat.S_IWUSR))
        with open(options["output"], "w", opener=opener) as fpo:
            content = render_to_string("imap_migration/offlineimap.conf", context)
            fpo.write(content)
