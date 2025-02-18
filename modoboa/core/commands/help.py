import sys

from . import Command


class HelpCommand(Command):

    help = "Display the help message associated to a specific command"  # NOQA:A003

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser.add_argument("name", type=str, help="A command name")

    def handle(self, parsed_args):
        if parsed_args.name not in self._commands:
            print(f"Unknown command: {parsed_args.name}", file=sys.stderr)
            sys.exit(1)
        cmd = self._commands[parsed_args.name](self._commands)
        cmd._parser.prog = f"modoboa-admin.py {parsed_args.name}"
        cmd._parser.description = cmd.help
        cmd._parser.print_help()
