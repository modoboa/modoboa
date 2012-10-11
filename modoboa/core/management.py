# coding: utf-8

from django.core import management
from django.conf import settings
from django.template import Context, Template
import argparse
import sys
import os
import shutil

class Command(object):
    
    def __init__(self):
        self._parser = argparse.ArgumentParser()
        if not settings.configured:
            settings.configure()

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

class DeployCommand(Command):

    def __init__(self):
        super(DeployCommand, self).__init__()
        self._parser.add_argument('name', type=str,
                                  help='The name of your Modoboa instance')

    def handle(self, parsed_args):
        management.call_command('startproject', parsed_args.name, verbosity=False)
        templates_dir = "%s/templates" % os.path.dirname(__file__)
        if os.path.exists("%(name)s/%(name)s" % {'name' : parsed_args.name}):
            # Django 1.4+
            path = "%(name)s/%(name)s" % {'name' : parsed_args.name}
            sys.path.append(parsed_args.name)
        else:
            path = parsed_args.name
            sys.path.append(".")
        mod = __import__(parsed_args.name, globals(), locals(), ['settings'])
        tpl = self._render_template("%s/settings.py" % templates_dir, {
                'secret_key' : mod.settings.SECRET_KEY,
                'name' : parsed_args.name
                })
        fp = open("%s/settings.py" % path, "w")
        fp.write(tpl)
        fp.close()
        shutil.copyfile("%s/urls.py" % templates_dir, "%s/urls.py" % path)
        

def handle_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', type=str,
                        help='A valid command name')
    (args, remaining) = parser.parse_known_args()

    try:
        cmd = globals()["%sCommand" % args.command.capitalize()]()
    except KeyError:
        print >>sys.stderr, "Unknown command '%s'" % args.command
        sys.exit(1)

    cmd.run(remaining)
