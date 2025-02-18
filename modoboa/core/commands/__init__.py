import argparse
import os
import sys

from django.conf import settings
from django.template import Context, Template
from django.utils.encoding import smart_str


class Command:
    """Base command class.

    A valid administrative command must inherit from this class.
    """

    help = "No help available."  # NOQA:A003

    def __init__(self, commands, verbose=False):
        self._commands = commands
        self._parser = argparse.ArgumentParser()
        self._verbose = verbose
        if not settings.configured:
            settings.configure(
                TEMPLATES=[
                    {"BACKEND": ("django.template.backends.django.DjangoTemplates")}
                ]
            )
        self._templates_dir = f"{os.path.dirname(__file__)}/templates"

    def _render_template(self, tplfile, env):
        """Render an HTML template."""
        with open(tplfile) as fp:
            tpl = Template(fp.read())
        return tpl.render(Context(env))

    def run(self, cmdline):
        args = self._parser.parse_args(cmdline)
        self.handle(args)

    def handle(self, parsed_args):
        """A command must overload this method to be called

        :param parsed_args:
        """
        raise NotImplementedError


def scan_for_commands(dirname=""):
    """Build a dictionnary containing all commands

    :param str dirname: the directory where commands are located
    :return: a dict of commands (name : class)
    """
    path = os.path.join(os.path.dirname(__file__), dirname)
    result = {}
    for f in os.listdir(path):
        if f in [".", "..", "__init__.py"]:
            continue
        if not f.endswith(".py"):
            continue
        if os.path.isfile(f):
            continue
        cmdname = f.replace(".py", "")
        cmdmod = __import__(
            "modoboa.core.commands", globals(), locals(), [smart_str(cmdname)]
        )
        cmdmod = getattr(cmdmod, cmdname)
        if "_" in cmdname:
            cmdclassname = "".join([s.capitalize() for s in cmdname.split("_")])
        else:
            cmdclassname = cmdname.capitalize()
        try:
            cmdclass = getattr(cmdmod, f"{cmdclassname}Command")
        except AttributeError:
            continue
        result[cmdname] = cmdclass
    return result


def handle_command_line():
    """Parse the command line."""
    commands = scan_for_commands()
    parser = argparse.ArgumentParser(
        description="A set of utilities to ease the installation of Modoboa.",
        epilog="""Available commands:
{}
""".format(
            "\n".join([f"\t{c}" for c in sorted(commands)])
        ),
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Activate verbose output"
    )
    parser.add_argument("command", type=str, help="A valid command name")
    (args, remaining) = parser.parse_known_args()

    if args.command not in commands:
        print(f"Unknown command '{args.command}'", file=sys.stderr)
        sys.exit(1)

    commands[args.command](commands, verbose=args.verbose).run(remaining)
