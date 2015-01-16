# coding: utf-8

import sys

from . import Command


class HelpCommand(Command):

    help = "Display the help message associated to a specific command"

    def __init__(self, *args, **kwargs):
        super(HelpCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument('name', type=str,
                                  help='A command name')

    def handle(self, parsed_args):
        if parsed_args.name not in self._commands:
            print >>sys.stderr, "Unknown command: %s" % parsed_args.name
            sys.exit(1)
        cmd = self._commands[parsed_args.name](self._commands)
        cmd._parser.prog = "modoboa-admin.py %s" % parsed_args.name
        cmd._parser.description = cmd.help
        cmd._parser.print_help()
