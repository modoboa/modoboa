# coding: utf-8
"""
A management command to clean unknown extensions from the
database.

"""
from django.conf import settings
from django.core.management.base import BaseCommand

from modoboa.core.models import Extension


class Command(BaseCommand):

    """Command definition."""

    help = "Clean unknowns extensions from the database"

    def handle(self, *args, **options):
        """Entry point."""
        for extension in Extension.objects.all():
            fullname = "modoboa.extensions.{}".format(extension.name)
            if not fullname in settings.MODOBOA_APPS:
                extension.delete()
