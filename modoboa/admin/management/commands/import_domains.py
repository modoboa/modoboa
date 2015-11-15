from optparse import make_option

from django.core.management.base import BaseCommand


from modoboa.core import load_core_settings
from modoboa.core.extensions import exts_pool

from ._import import import_csv


class Command(BaseCommand):
    args = 'csvfile'
    help = 'Import domains and domain aliases from a csv file'

    option_list = BaseCommand.option_list + (
        make_option(
            '--sepchar', action='store_true', dest='sepchar', default=';'
        ),
        make_option(
            '--continue-if-exists', action='store_true',
            dest='continue_if_exists', default=True
        )
    )

    def handle(self, *args, **kwargs):
        exts_pool.load_all()
        load_core_settings()

        for filename in args:
            import_csv(filename, kwargs)
