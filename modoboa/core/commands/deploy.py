# coding: utf-8
import getpass
import os
import shutil
import sys

import subprocess

from django.core import management
from django.template import Context, Template

import dj_database_url

from modoboa.lib.sysutils import exec_cmd
from modoboa.core.commands import Command

DBCONN_TPL = """
    '{{ conn_name }}': {
        'ENGINE': '{{ ENGINE }}',
        'NAME': '{{ NAME }}',
        'USER': '{% if USER %}{{ USER }}{% endif %}',
        'PASSWORD': '{% if PASSWORD %}{{ PASSWORD }}{% endif %}',
        'HOST': '{% if HOST %}{{ HOST }}{% endif %}',
        'PORT': '{% if PORT %}{{ PORT }}{% endif %}',
        {% if ENGINE == 'django.db.backends.mysql' %}'OPTIONS' : {
            "init_command" : 'SET foreign_key_checks = 0;',
        },{% endif %}
    },
"""


class DeployCommand(Command):

    """The ``deploy`` command."""

    help = (
        "Create a fresh django project (calling startproject)"
        " and apply Modoboa specific settings."
    )

    def __init__(self, *args, **kwargs):
        super(DeployCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument('name', type=str,
                                  help='The name of your Modoboa instance')
        self._parser.add_argument(
            '--with-amavis', action='store_true', default=False,
            help='Include amavis configuration'
        )
        self._parser.add_argument(
            '--dbaction', type=str, default="install",
            help='Action to take on the database (install|upgrade)'
        )
        self._parser.add_argument(
            '--collectstatic', action='store_true', default=False,
            help='Run django collectstatic command'
        )
        self._parser.add_argument(
            '--dburl', type=str, nargs=1, default=None,
            help='The database-url for your modoboa instance')
        self._parser.add_argument(
            '--amavis_dburl', type=str, nargs=1, default=None,
            help='The database-url for your amavis instance')
        self._parser.add_argument(
            '--domain', type=str, default=None,
            help='The domain under which you want to deploy modoboa')
        self._parser.add_argument(
            '--extensions', type=str, nargs='*',
            help='Deploy with those extensions already enabled'
        )
        self._parser.add_argument(
            '--lang', type=str, default="en-us",
            help="Set the default language"
        )
        self._parser.add_argument(
            '--timezone', type=str, default="UTC",
            help="Set the local timezone"
        )
        self._parser.add_argument(
            '--devel', action='store_true', default=False,
            help='Create a development instance'
        )

    def _exec_django_command(self, name, cwd, *args):
        """Run a django command for the freshly created project

        :param name: the command name
        :param cwd: the directory where the command must be executed
        """
        cmd = 'python manage.py %s %s' % (name, " ".join(args))
        if not self._verbose:
            p = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                shell=True, cwd=cwd
            )
            output = p.communicate()
        else:
            p = subprocess.Popen(cmd, shell=True, cwd=cwd)
            p.wait()
            output = None
        if p.returncode:
            if output:
                print >> sys.stderr, "\n".join(
                    [l for l in output if l is not None])
            print >> sys.stderr, "%s failed, check your configuration" % cmd

    def ask_db_info(self, name='default'):
        """Prompt the user for database information

        Gather all information required to create a new database
        connection (into settings.py).

        :param name: the connection name
        """
        print "Configuring database connection: %s" % name
        info = {
            'conn_name': name,
            'ENGINE': raw_input('Database type (mysql, postgres or sqlite3): ')
        }
        if info['ENGINE'] not in ['mysql', 'postgres', 'sqlite3']:
            raise RuntimeError('Unsupported database engine')

        if info['ENGINE'] == 'sqlite3':
            info['ENGINE'] = 'django.db.backends.sqlite3'
            info['NAME'] = '%s.db' % name
            return info
        if info['ENGINE'] == 'postgres':
            info['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
            default_port = 5432
        else:
            info['ENGINE'] = 'django.db.backends.mysql'
            default_port = 3306
        info['HOST'] = raw_input("Database host (default: 'localhost'): ")
        info['PORT'] = raw_input(
            "Database port (default: '%s'): " % default_port)
        # leave port setting empty, if default value is supplied and
        # leave it to django
        if info['PORT'] == default_port:
            info['PORT'] = ''
        info['NAME'] = raw_input('Database name: ')
        info['USER'] = raw_input('Username: ')
        info['PASSWORD'] = getpass.getpass('Password: ')
        return info

    def handle(self, parsed_args):
        management.call_command(
            'startproject', parsed_args.name, verbosity=False
        )
        path = "%(name)s/%(name)s" % {'name': parsed_args.name}
        sys.path.append(parsed_args.name)

        t = Template(DBCONN_TPL)

        if parsed_args.dburl:
            info = dj_database_url.config(default=parsed_args.dburl[0])
            # In case the user fails to supply a valid database url,
            # fallback to manual mode
            if not info:
                print "There was a problem with your database-url. \n"
                info = self.ask_db_info()
            # If we set this earlier, our fallback method will never
            # be triggered
            info['conn_name'] = 'default'
        else:
            info = self.ask_db_info()

        default_conn = t.render(Context(info))

        if parsed_args.with_amavis:
            if parsed_args.amavis_dburl:
                amavis_info = dj_database_url.config(
                    default=parsed_args.amavis_dburl[0])
                # In case the user fails to supply a valid database
                # url, fallback to manual mode
                if not amavis_info:
                    amavis_info = self.ask_db_info('amavis')
                # If we set this earlier, our fallback method will
                # never be triggered
                amavis_info['conn_name'] = 'amavis'
            else:
                amavis_info = self.ask_db_info('amavis')

            amavis_conn = t.render(Context(amavis_info))
        else:
            amavis_conn = None

        if parsed_args.domain:
            allowed_host = parsed_args.domain
        else:
            allowed_host = raw_input(
                'What will be the hostname used to access Modoboa? '
            )
            if not allowed_host:
                allowed_host = "localhost"

        bower_components_dir = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../bower_components")
        )

        mod = __import__(parsed_args.name, globals(), locals(), ['settings'])
        tpl = self._render_template(
            "%s/settings.py.tpl" % self._templates_dir, {
                'default_conn': default_conn, 'amavis_conn': amavis_conn,
                'secret_key': mod.settings.SECRET_KEY,
                'name': parsed_args.name,
                'allowed_host': allowed_host,
                'lang': parsed_args.lang,
                'timezone': parsed_args.timezone,
                'bower_components_dir': bower_components_dir,
                'devmode': parsed_args.devel
            }
        )
        with open("%s/settings.py" % path, "w") as fp:
            fp.write(tpl)
        shutil.copyfile(
            "%s/urls.py.tpl" % self._templates_dir, "%s/urls.py" % path
        )
        os.mkdir("%s/media" % parsed_args.name)

        os.unlink("%s/settings.pyc" % path)
        if parsed_args.dbaction == "install":
            self._exec_django_command(
                "syncdb", parsed_args.name, '--noinput'
            )
            exec_cmd('sed -ri "s|^#(\s+\'south)|\\1|" %s/settings.py' % path)
            self._exec_django_command(
                "syncdb", parsed_args.name,
            )
            self._exec_django_command(
                'migrate', parsed_args.name, '--fake'
            )
            self._exec_django_command(
                "loaddata", parsed_args.name, 'initial_users.json'
            )
        elif parsed_args.dbaction == "upgrade":
            exec_cmd('sed -ri "s|^#(\s+\'south)|\\1|" %s/settings.py' % path)
            self._exec_django_command(
                "syncdb", parsed_args.name, "--migrate"
            )

        if parsed_args.collectstatic:
            self._exec_django_command(
                "collectstatic", parsed_args.name, '--noinput'
            )

        if parsed_args.extensions:
            self._exec_django_command(
                "manage_extensions", parsed_args.name, *parsed_args.extensions
            )

        self._exec_django_command(
            "set_default_site", parsed_args.name, allowed_host
        )
