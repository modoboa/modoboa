# coding: utf-8

from django.conf import settings
from django.template import Context, Template
import argparse
import os
import sys

class Command(object):
    
    def __init__(self):
        self._parser = argparse.ArgumentParser()
        if not settings.configured:
            settings.configure()
        self._templates_dir = "%s/templates" % os.path.dirname(__file__)

    def _render_template(self, tplfile, env):
        fp = open(tplfile)
        t = Template(fp.read())
        fp.close()
        return t.render(Context(env))

    def run(self, cmdline):
        args = self._parser.parse_args(cmdline)
        self.handle(args)

    def handle(self, parsed_args):
        raise NotImplemented

def handle_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str,
                        help='A valid command name')
    (args, remaining) = parser.parse_known_args()


    try:
        cmdmod = __import__("modoboa.core.commands", globals(), locals(),
                            [args.command])
        cmdmod = getattr(cmdmod, args.command)
        cmdclass = getattr(cmdmod, "%sCommand" % args.command.capitalize())
        cmd = cmdclass()
    except ImportError:
        print >>sys.stderr, "Unknown command '%s'" % args.command
        sys.exit(1)

    cmd.run(remaining)
