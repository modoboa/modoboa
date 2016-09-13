# -*- coding: utf-8 -*-
"""Management command to check defined domains against MX records."""

from django.core.management.base import BaseCommand

from modoboa.admin import models
from modoboa.admin.lib import get_mx_records_for_domain


class CheckMXRecords(BaseCommand):
    """Command class."""

    help = "Check defined domains against MX records."

    def handle(self, *args, **options):
        """Command entry point."""
        for domain in models.Domain.objects.all():
            for record in get_mx_records_for_domain(domain):
                print(record)
