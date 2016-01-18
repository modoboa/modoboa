from optparse import make_option

from django.core.management.base import BaseCommand

from modoboa.core.extensions import exts_pool

from ._import import import_csv


class Command(BaseCommand):
    args = 'csvfile'
    help = 'Import identities from a csv file'

    def add_arguments(self, parser):
        """Add extra arguments to command."""
        parser.add_argument(
            "--sepchar", type=str, default=";",
            help="Separator used in file.")
        parser.add_argument(
            "--continue-if-exists", action="store_true",
            dest='continue_if_exists', default=True,
            help="Continue even if an entry already exists.")
        parser.add_argument(
            "--crypt-password", action="store_true", dest="crypt_password",
            default=False, help="Encrypt provided passwords.")

    def handle(self, *args, **options):
        exts_pool.load_all()
        for filename in args:
            import_csv(filename, options)
