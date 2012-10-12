import sys
import os
import shutil
from django.core import management
from modoboa.core.management import Command

class DeployCommand(Command):

    def __init__(self):
        super(DeployCommand, self).__init__()
        self._parser.add_argument('name', type=str,
                                  help='The name of your Modoboa instance')

    def handle(self, parsed_args):
        management.call_command('startproject', parsed_args.name, verbosity=False)
        if os.path.exists("%(name)s/%(name)s" % {'name' : parsed_args.name}):
            # Django 1.4+
            path = "%(name)s/%(name)s" % {'name' : parsed_args.name}
            sys.path.append(parsed_args.name)
        else:
            path = parsed_args.name
            sys.path.append(".")
        mod = __import__(parsed_args.name, globals(), locals(), ['settings'])
        tpl = self._render_template("%s/settings.py" % self._templates_dir, {
                'secret_key' : mod.settings.SECRET_KEY,
                'name' : parsed_args.name
                })
        fp = open("%s/settings.py" % path, "w")
        fp.write(tpl)
        fp.close()
        shutil.copyfile("%s/urls.py" % self._templates_dir, "%s/urls.py" % path)
        
