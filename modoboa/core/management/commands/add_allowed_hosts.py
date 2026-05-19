from django.core.management.base import BaseCommand, CommandError

from modoboa.core.utils import add_allowed_hosts


class Command(BaseCommand):
    """Command class."""

    help = "Add new allowed hosts to frontend Oauth2 application."

    def add_arguments(self, parser):
        parser.add_argument("hostnames", type=str, nargs="+")

    def handle(self, *args, **options):
        if not add_allowed_hosts(options["hostnames"]):
            raise CommandError(
                "Application modoboa_frontend not found. "
                "Make sure you ran load_initial_data first."
            )
