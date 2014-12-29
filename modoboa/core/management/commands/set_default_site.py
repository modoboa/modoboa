# coding: utf-8
"""
A simple managemenent command to update the default site.

See `https://docs.djangoproject.com/en/dev/ref/contrib/sites/`_.
"""

from django.core.management.base import BaseCommand, CommandError

from django.contrib.sites.models import Site

from . import CloseConnectionMixin


class Command(BaseCommand, CloseConnectionMixin):

    """Management command to set the default site."""

    help = 'Set default site (see django.contrib.sites)'

    def handle(self, *args, **options):
        """Command entry point."""
        if not args:
            raise CommandError("You must provide a hostname")
        site = Site.objects.get(pk=1)
        site.domain = args[0]
        site.name = args[0]
        site.save()
