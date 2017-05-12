"""Modoboa main management command."""

from __future__ import unicode_literals

from subcommand.base import SubcommandCommand

from .subcommands._mx import CheckMXRecords
from .subcommands._export import ExportCommand
from .subcommands._import import ImportCommand
from .subcommands._repair import Repair


class Command(SubcommandCommand):
    """Top management command for modoboa.

    $ python manage.py modo
    """

    help = "Modoboa top management command."

    subcommands = {
        "export": ExportCommand,
        "import": ImportCommand,
        "check_mx": CheckMXRecords,
        "repair": Repair,
    }
