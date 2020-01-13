"""
A simple managemenent command to update the default site.

See `https://docs.djangoproject.com/en/dev/ref/contrib/sites/`_.
"""

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    """Management command to set the default site."""

    help = "Set default site (see django.contrib.sites)"  # NOQA:A003

    def add_arguments(self, parser):
        """Define command arguments."""
        parser.add_argument("hostname", type=str)

    def handle(self, *args, **options):
        """Command entry point."""
        if "hostname" not in options:
            raise CommandError("You must provide a hostname")
        site = Site.objects.get(pk=1)
        site.domain = options["hostname"]
        site.name = options["hostname"]
        site.save()
