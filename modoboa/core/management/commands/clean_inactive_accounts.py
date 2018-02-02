# -*- coding: utf-8 -*-

"""Inactive accounts cleanup tool."""

from __future__ import print_function, unicode_literals

from dateutil.relativedelta import relativedelta
from six.moves import input

from django.core.management.base import BaseCommand
from django.utils import timezone

from modoboa.parameters import tools as param_tools
from ... import models


class Command(BaseCommand):
    """Management command to clean inactive accounts."""

    help = "Inactive accounts cleanup"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command line."""
        parser.add_argument(
            "--delete", action="store_true", default=False,
            help="Delete inactive accounts (default is to disable)")
        parser.add_argument(
            "--dry-run", action="store_true", default=False,
            help="Only look for inactive accounts, no action")
        parser.add_argument(
            "--silent", action="store_true", default=False,
            help="Enable silent mode (no question)")
        parser.add_argument(
            "--verbose", action="store_true", default=False,
            help="Enable verbose mode")

    def _log_inactive_accounts(self, qset):
        """Log inactive accounts found."""
        print(
            "The following inactive accounts have been found:",
            file=self.stdout)
        for account in qset.values("username", "last_login"):
            print(
                "> {}\n    (last login: {})".format(
                    account["username"], account["last_login"]),
                file=self.stdout
            )

    def handle(self, *args, **options):
        """Command entry point."""
        inactive_account_threshold = param_tools.get_global_parameter(
            "inactive_account_threshold")
        qset = models.User.objects.filter(
            is_active=True, is_superuser=False,
            last_login__lt=timezone.now() -
            relativedelta(days=inactive_account_threshold))
        if not qset.exists():
            return
        if options["verbose"]:
            self._log_inactive_accounts(qset)
        if options["dry_run"]:
            return
        action = "delete" if options["delete"] else "disable"
        if not options["silent"]:
            answer = input(
                "Do you want to {} those accounts? (y/N) ".format(action))
            if not answer.lower().startswith("y"):
                return
        if action == "disable":
            qset.update(is_active=False)
        else:
            qset.delete()
