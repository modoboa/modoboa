"""Management command to import contacts from a CSV file."""

from django.core.management.base import BaseCommand, CommandError

from modoboa.contacts import models
from modoboa.contacts.importer import import_csv_file


class Command(BaseCommand):
    """Management command to import contacts."""

    help = "Import contacts from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delimiter", type=str, default=",", help="Delimiter used in CSV file"
        )
        parser.add_argument(
            "--carddav-password",
            type=str,
            default=None,
            help=(
                "Password associated to email. If provided, imported "
                "contacts will be synced to CardDAV servert too"
            ),
        )
        parser.add_argument(
            "--backend",
            type=str,
            default="auto",
            help=(
                "Specify import backend to use. Defaults to 'auto', "
                "meaning the script will try to guess which one to use"
            ),
        )
        parser.add_argument(
            "email", type=str, help="Email address to import contacts for"
        )
        parser.add_argument("file", type=str, help="Path of the CSV file to import")

    def handle(self, *args, **options):
        addressbook = models.AddressBook.objects.filter(
            user__email=options["email"]
        ).first()
        if not addressbook:
            raise CommandError(
                "Address Book for email '{}' not found".format(options["email"])
            )
        try:
            import_csv_file(
                addressbook,
                options["backend"],
                options["file"],
                options["delimiter"],
                options.get("carddav_password"),
            )
        except RuntimeError as err:
            raise CommandError(err) from None
        self.stdout.write(self.style.SUCCESS("File was imported successfuly"))
