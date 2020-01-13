"""Django management command to export admin objects."""

import csv

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_text

from modoboa.core.extensions import exts_pool
from modoboa.core.models import User
from .... import models


class ExportCommand(BaseCommand):
    """Command class."""

    help = "Export domains or identities using CSV format"  # NOQA:A003

    def add_arguments(self, parser):
        """Add arguments to command."""
        parser.add_argument(
            "--sepchar", type=str, dest="sepchar", default=";",
            help="Separator used in generated file."
        )
        parser.add_argument(
            "objtype", type=str, choices=["domains", "identities"],
            help="The type of object to export (domains or identities)")

    def export_domains(self):
        """Export all domains."""
        for dom in models.Domain.objects.all():
            dom.to_csv(self.csvwriter)

    def export_identities(self):
        """Export all identities."""
        for u in User.objects.all():
            u.to_csv(self.csvwriter)
        dumped_aliases = []
        qset = (
            models.Alias.objects.exclude(alias_recipient_aliases=None)
            .distinct().prefetch_related("aliasrecipient_set")
        )
        for alias in qset:
            alias.to_csv(self.csvwriter)
            dumped_aliases += [alias.pk]
        qset = (
            models.Alias.objects.exclude(pk__in=dumped_aliases)
            .prefetch_related("aliasrecipient_set")
        )
        for alias in qset:
            alias.to_csv(self.csvwriter)

    def handle(self, *args, **options):
        exts_pool.load_all()
        self.csvwriter = csv.writer(
            self.stdout, delimiter=smart_text(options["sepchar"]))
        getattr(self, "export_{}".format(options["objtype"]))()
