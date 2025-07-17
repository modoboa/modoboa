import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from modoboa.core.models import Log
from modoboa.parameters import tools as param_tools

JOB_IDs = ["clearsessions_r", "cleanlogs_r", "logparser_r"]
AMAVIS_IDs = ["qcleanup_r", "amnotify_r"]


class Command(BaseCommand):
    """Command class."""

    help = "Checks that redondants jobs are started or start them"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--queue-now",
            action="store_true",
            default=False,
            help="Queue all redondant job now",
        )

    def check_clean_log(queue_now=False):
        pass

    def handle(self, *args, **options):
        self.check_clean_log(options["queue_now"])
