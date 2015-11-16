import sys
import csv
from optparse import make_option

from django.core.management.base import BaseCommand

from modoboa.core import load_core_settings
from modoboa.core.models import User
from modoboa.core.extensions import exts_pool
from ...models import Alias


class Command(BaseCommand):
    help = 'Export identities (mailbox and aliases) to a csv'

    option_list = BaseCommand.option_list + (
        make_option(
            '--sepchar', action='store_true', dest='sepchar', default=';'
        ),
    )

    def handle(self, *args, **kwargs):
        exts_pool.load_all()
        load_core_settings()

        csvwriter = csv.writer(sys.stdout, delimiter=kwargs['sepchar'])
        for u in User.objects.all():
            u.to_csv(csvwriter)

        for a in Alias.objects.prefetch_related('mboxes', 'aliases'):
            a.to_csv(csvwriter)
