# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from modoboa.core.models import Log
from modoboa.parameters import tools as param_tools


class Command(BaseCommand):
    """Command class."""

    help = "Log table cleanup"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--debug", action="store_true", default=False,
            help="Activate debug output")
        parser.add_argument(
            "--verbose", action="store_true", default=False,
            help="Display informational messages")

    def __vprint(self, msg):
        if not self.verbose:
            return
        print(msg)

    def handle(self, *args, **options):
        if options["debug"]:
            log = logging.getLogger("django.db.backends")
            log.setLevel(logging.DEBUG)
            log.addHandler(logging.StreamHandler())
        self.verbose = options["verbose"]

        log_maximum_age = param_tools.get_global_parameter("log_maximum_age")
        self.__vprint("Deleting logs older than %d days..." % log_maximum_age)
        limit = timezone.now() - datetime.timedelta(log_maximum_age)
        Log.objects.filter(date_created__lt=limit).delete()
        self.__vprint("Done.")
