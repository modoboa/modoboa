"""Import a DMARC aggregated report."""

from django.core.management.base import BaseCommand

from ... import lib


class Command(BaseCommand):
    """Command definition."""

    help = "Import DMARC aggregated reports."

    def add_arguments(self, parser):
        """Add extra arguments to parser."""
        parser.add_argument(
            "--pipe",
            action="store_true",
            default=False,
            help="Import a report from an email given on stdin",
        )
        parser.add_argument(
            "--imap",
            action="store_true",
            default=False,
            help="Import a report from an IMAP mailbox",
        )
        parser.add_argument("--host", default="localhost", help="IMAP host")
        parser.add_argument(
            "--ssl", action="store_true", default=False, help="Connect using SSL"
        ),
        parser.add_argument(
            "--mailbox", default="INBOX", help="IMAP mailbox to import reports from"
        )

    def handle(self, *args, **options):
        """Entry point."""
        if options.get("pipe"):
            lib.import_report_from_stdin()
        elif options.get("imap"):
            lib.import_from_imap(options)
        else:
            print("Nothing to do.")
