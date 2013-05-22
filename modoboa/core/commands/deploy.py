# coding: utf-8
import sys
import os
import shutil
import getpass
import subprocess
from django.core import management
from django.template import Context, Template
from modoboa.core.management import Command

dbconn_tpl = """
    '{{ conn_name }}': {
        'ENGINE': 'django.db.backends.{{ dbtype }}',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '{{ dbname }}',                       # Or path to database file if using sqlite3.
        'USER': '{{ username }}',                     # Not used with sqlite3.
        'PASSWORD': '{{ password }}',                 # Not used with sqlite3.
        'HOST': '{{ dbhost }}',                       # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.{% if dbtype == 'mysql' %}
        'OPTIONS' : {
            "init_command" : 'SET foreign_key_checks = 0;',
        },{% endif %}
    },
"""

class DeployCommand(Command):
    help = "Create a fresh django project (calling startproject) and apply Modoboa specific settings."

    def __init__(self, *args, **kwargs):
        super(DeployCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument('name', type=str,
                                  help='The name of your Modoboa instance')
        self._parser.add_argument('--with-amavis', action='store_true', default=False,
                                  help='Include amavis configuration')
        self._parser.add_argument('--syncdb', action='store_true', default=False,
                                  help='Run django syncdb command')
        self._parser.add_argument('--collectstatic', action='store_true', default=False,
                                  help='Run django collectstatic command')

    def _exec_django_command(self, name, cwd, *args):
        """Run a django command for the freshly created project

        :param name: the command name
        :param cwd: the directory where the command must be executed
        """
        cmd = 'python manage.py %s %s' % (name, " ".join(args))
        if not self._verbose:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 shell=True, cwd=cwd)
            output = p.communicate()
        else:
            p = subprocess.Popen(cmd, shell=True, cwd=cwd)
            p.wait()
            output = None
        if p.returncode:
            if output:
                print >>sys.stderr, "\n".join(filter(lambda l: l is not None, output))
            print >>sys.stderr, "%s failed, check your configuration" % cmd

    def ask_db_info(self, name='default'):
        """Prompt the user for database information

        Gather all information required to create a new database
        connection (into settings.py).

        :param name: the connection name
        """
        print "Configuring database connection: %s" % name
        info = {'conn_name': name, 'dbtype': raw_input('Database type (mysql or postgres): ')}
        if info['dbtype'] not in ['mysql', 'postgres']:
            info['dbtype'] = 'mysql'
        if info['dbtype'] == 'postgres':
            info['dbtype'] = 'postgresql_psycopg2'
        info['dbhost'] = raw_input('Database host (default: localhost): ')
        if info['dbhost'] == '':
            info['dbhost'] = 'localhost'
        info['dbname'] = raw_input('Database name: ')
        info['username'] = raw_input('Username: ')
        info['password'] = getpass.getpass('Password: ')
        return info

    def handle(self, parsed_args):
        management.call_command('startproject', parsed_args.name, verbosity=False)
        if os.path.exists("%(name)s/%(name)s" % {'name' : parsed_args.name}):
            # Django 1.4+
            path = "%(name)s/%(name)s" % {'name' : parsed_args.name}
            sys.path.append(parsed_args.name)
            django14 = True
        else:
            path = parsed_args.name
            sys.path.append(".")
            django14 = False

        t = Template(dbconn_tpl)
        default_conn = t.render(Context(self.ask_db_info()))
        amavis_conn = t.render(Context(self.ask_db_info('amavis'))) if parsed_args.with_amavis \
            else None

        allowed_host = raw_input('Under which domain do you want to deploy modoboa? ')

        mod = __import__(parsed_args.name, globals(), locals(), ['settings'])
        tpl = self._render_template("%s/settings.py" % self._templates_dir, {
            'default_conn' : default_conn, 'amavis_conn' : amavis_conn,
            'secret_key' : mod.settings.SECRET_KEY,
            'name' : parsed_args.name, 'django14' : django14,
            'allowed_host': allowed_host
            })
        fp = open("%s/settings.py" % path, "w")
        fp.write(tpl)
        fp.close()
        shutil.copyfile("%s/urls.py" % self._templates_dir, "%s/urls.py" % path)
        os.mkdir("%s/media" % path)

        if parsed_args.syncdb:
            self._exec_django_command("syncdb", parsed_args.name, '--migrate', '--noinput')
            self._exec_django_command("loaddata", parsed_args.name, 'initial_users.json')

        if parsed_args.collectstatic:
            self._exec_django_command("collectstatic", parsed_args.name, '--noinput')
