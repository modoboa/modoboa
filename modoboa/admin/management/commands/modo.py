"""Modoboa main management command."""

from django.core.management.base import BaseCommand

from .subcommands._export import ExportCommand
from .subcommands._import import ImportCommand
from .subcommands._manage_dkim_keys import ManageDKIMKeys
from .subcommands._mx import CheckMXRecords
from .subcommands._repair import Repair


class Command(BaseCommand):
    """Top management command for modoboa.

    $ python manage.py modo
    """

    help = "Modoboa top management command."

    subcommands = {
        "export": ExportCommand,
        "import": ImportCommand,
        "check_mx": CheckMXRecords,
        "manage_dkim_keys": ManageDKIMKeys,
        "repair": Repair,
    }

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            dest='subcommand', title='subcommands'
        )
        # required argument is added in Python 3.7
        subparsers.required = True

        for command_name, command_class in self.subcommands.items():
            command = command_class(self.stdout, self.stderr)
            command.style = self.style

            subparser = subparsers.add_parser(
                command_name, help=command_class.help
            )
            # This is needed to output console friendly errors
            subparser.called_from_command_line = self._called_from_command_line

            command.add_arguments(subparser)

            subparser.set_defaults(command=command)

    def execute(self, *args, **options):
        return options.pop('command').execute(*args, **options)
