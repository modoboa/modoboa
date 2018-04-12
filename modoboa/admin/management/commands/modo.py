# -*- coding: utf-8 -*-

"""Modoboa main management command."""

from __future__ import unicode_literals

from subcommand.base import SubcommandCommand

from .subcommands._export import ExportCommand
from .subcommands._import import ImportCommand
from .subcommands._manage_dkim_keys import ManageDKIMKeys
from .subcommands._mx import CheckMXRecords
from .subcommands._repair import Repair


class Command(SubcommandCommand):
    """Top management command for modoboa.

    $ python manage.py modo
    """

    help = "Modoboa top management command."  # NOQA:A003

    subcommands = {
        "export": ExportCommand,
        "import": ImportCommand,
        "check_mx": CheckMXRecords,
        "manage_dkim_keys": ManageDKIMKeys,
        "repair": Repair,
    }
