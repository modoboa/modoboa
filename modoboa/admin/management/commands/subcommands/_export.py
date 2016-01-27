"""Django management command to export admin objects."""

import csv
import sys

from django.core.management.base import BaseCommand

from modoboa.core.models import User
from modoboa.core.extensions import exts_pool
from .... import models


class ExportCommand(BaseCommand):
    """Command class."""

    help = "Export domains or identities using CSV format"

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
            models.AliasRecipient.objects.filter(r_alias__isnull=False)
            .distinct("r_alias")
            .select_related("r_alias")
            .prefetch_related("r_alias__aliasrecipient_set")
        )
        for alr in qset:
            alr.r_alias.to_csv(self.csvwriter)
            dumped_aliases += [alr.r_alias.pk]
        qset = (
            models.Alias.objects.exclude(pk__in=dumped_aliases)
            .prefetch_related('aliasrecipient_set')
        )
        for alias in qset:
            alias.to_csv(self.csvwriter)

    def handle(self, *args, **options):
        exts_pool.load_all()
        self.csvwriter = csv.writer(sys.stdout, delimiter=options['sepchar'])
        getattr(self, "export_{}".format(options["objtype"]))()
