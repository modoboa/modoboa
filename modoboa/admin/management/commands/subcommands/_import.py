# -*- coding: utf-8 -*-

"""Django management command to import admin objects."""

from __future__ import unicode_literals

import io
import os

import progressbar

from django.core.management.base import BaseCommand, CommandError
from django.utils import six

from modoboa.core import models as core_models
from modoboa.core.extensions import exts_pool
from modoboa.lib.exceptions import Conflict
from .... import signals

if six.PY2:
    from backports import csv
else:
    import csv


class ImportCommand(BaseCommand):
    """Command class."""

    args = "csvfile"
    help = "Import identities from a csv file"  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--sepchar", type=six.text_type, default=";",
            help="Separator used in file.")
        parser.add_argument(
            "--continue-if-exists", action="store_true",
            dest="continue_if_exists", default=False,
            help="Continue even if an entry already exists.")
        parser.add_argument(
            "--crypt-password", action="store_true",
            default=False, help="Encrypt provided passwords.")
        parser.add_argument(
            "files", type=six.text_type, nargs="+", help="CSV files to import.")

    def _import(self, filename, options):
        """Import domains or identities."""
        superadmin = (
            core_models.User.objects.filter(is_superuser=True).first()
        )
        if not os.path.isfile(filename):
            raise CommandError("File not found")

        num_lines = sum(
            1 for line in io.open(filename, encoding="utf-8") if line
        )
        pbar = progressbar.ProgressBar(
            widgets=[
                progressbar.Percentage(), progressbar.Bar(), progressbar.ETA()
            ], maxval=num_lines
        ).start()
        with io.open(filename, encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=options["sepchar"])
            i = 0
            for row in reader:
                if not row:
                    continue
                fct = signals.import_object.send(
                    sender=self.__class__, objtype=row[0].strip())
                fct = [func for x_, func in fct if func is not None]
                if not fct:
                    continue
                fct = fct[0]
                try:
                    fct(superadmin, row, options)
                except Conflict:
                    if options["continue_if_exists"]:
                        continue
                    raise CommandError(
                        "Object already exists: {}".format(
                            options["sepchar"].join(row[:2])))
                i += 1
                pbar.update(i)

        pbar.finish()

    def handle(self, *args, **options):
        """Command entry point."""
        exts_pool.load_all()
        for filename in options["files"]:
            self._import(filename, options)
