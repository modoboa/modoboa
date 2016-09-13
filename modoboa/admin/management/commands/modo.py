"""Modoboa main management command."""

from subcommand.base import SubcommandCommand

from .subcommands._dnsbl import CheckDNSBLCommand
from .subcommands._mx import CheckMXRecords
from .subcommands._export import ExportCommand
from .subcommands._import import ImportCommand


class Command(SubcommandCommand):
    """Top management command for modoboa.

    $ python manage.py modo
    """

    help = "Modoboa top management command."

    subcommands = {
        "export": ExportCommand,
        "import": ImportCommand,
        "check_mx": CheckMXRecords,
        "check_dnsbl": CheckDNSBLCommand,
    }
