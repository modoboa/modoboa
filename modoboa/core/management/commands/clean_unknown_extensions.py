# coding: utf-8
"""
A management command to clean unknown extensions from the
database.

"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from modoboa.core.models import Extension


class Command(BaseCommand):

    """Command definition."""

    help = "Clean unknowns extensions from the database"

    def handle(self, *args, **options):
        """Entry point."""
        for extension in Extension.objects.all():
            fullname = "modoboa.extensions.{0}".format(extension.name)
            if not fullname in settings.MODOBOA_APPS:
                extension.delete()
        connection.close()
