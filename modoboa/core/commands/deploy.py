"""A shortcut to deploy a fresh modoboa instance."""

import getpass
import os
from os.path import isfile
import shutil
import subprocess
import sys

import dj_database_url

import django
from django.core import management
from django.template import Context, Template
from django.utils.encoding import smart_str

from modoboa.core.commands import Command
from modoboa.core.utils import generate_rsa_private_key
from modoboa.lib.api_client import ModoAPIClient
from modoboa.lib.sysutils import exec_cmd

DBCONN_TPL = """
    '{{ conn_name }}': {
        'ENGINE': '{{ ENGINE }}',
        'NAME': '{{ NAME }}',
        'USER': '{% if USER %}{{ USER }}{% endif %}',
        'PASSWORD': '{% if PASSWORD %}{{ PASSWORD }}{% endif %}',
        'HOST': '{% if HOST %}{{ HOST }}{% endif %}',
        'PORT': '{% if PORT %}{{ PORT }}{% endif %}',
        'ATOMIC_REQUESTS': True,
        {% if ENGINE == 'django.db.backends.mysql' %}'OPTIONS' : {
            "init_command" : 'SET foreign_key_checks = 0;',
        },{% endif %}
    },
"""


class DeployCommand(Command):
    """The ``deploy`` command."""

    help = (  # NOQA:A003
        "Create a fresh django project (calling startproject)"
        " and apply Modoboa specific settings."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parser.add_argument(
            "name", type=str, help="The name of your Modoboa instance"
        )
        self._parser.add_argument(
            "--collectstatic",
            action="store_true",
            default=False,
            help="Run django collectstatic command",
        )
        self._parser.add_argument(
            "--dburl",
            type=str,
            nargs="+",
            default=None,
            help="A database-url with a name",
        )
        self._parser.add_argument(
            "--domain",
            type=str,
            default=None,
            help="The domain under which you want to deploy modoboa",
        )
        self._parser.add_argument(
            "--lang", type=str, default="en", help="Set the default language"
        )
        self._parser.add_argument(
            "--timezone", type=str, default="UTC", help="Set the local timezone"
        )
        self._parser.add_argument(
            "--devel",
            action="store_true",
            default=False,
            help="Create a development instance",
        )
        self._parser.add_argument(
            "--extensions", type=str, nargs="*", help="The list of extension to deploy"
        )
        self._parser.add_argument(
            "--dont-install-extensions",
            action="store_true",
            default=False,
            help="Do not install extensions using pip",
        )
        self._parser.add_argument(
            "--admin-username",
            default="admin",
            help="Username of the initial super administrator",
        )

    def _exec_django_command(self, name, cwd, *args):
        """Run a django command for the freshly created project

        :param name: the command name
        :param cwd: the directory where the command must be executed
        """
        cmd = [sys.executable, "manage.py", name]
        cmd.extend(args)
        if not self._verbose:
            p = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd
            )
            output = p.communicate()
        else:
            p = subprocess.Popen(cmd, cwd=cwd)
            p.wait()
            output = None
        if p.returncode:
            if output:
                print(
                    "\n".join([line.decode() for line in output if line is not None]),
                    file=sys.stderr,
                )
            print(f"{cmd} failed, check your configuration", file=sys.stderr)

    def ask_db_info(self, name="default"):
        """Prompt the user for database information

        Gather all information required to create a new database
        connection (into settings.py).

        :param name: the connection name
        """
        print(f"Configuring database connection: {name}")
        info = {
            "conn_name": name,
            "ENGINE": input("Database type (mysql, postgres or sqlite3): "),
        }
        if info["ENGINE"] not in ["mysql", "postgres", "sqlite3"]:
            raise RuntimeError("Unsupported database engine")

        if info["ENGINE"] == "sqlite3":
            info["ENGINE"] = "django.db.backends.sqlite3"
            info["NAME"] = f"{name}.db"
            return info
        if info["ENGINE"] == "postgres":
            info["ENGINE"] = "django.db.backends.postgresql"
            default_port = 5432
        else:
            info["ENGINE"] = "django.db.backends.mysql"
            default_port = 3306
        info["HOST"] = input("Database host (default: 'localhost'): ")
        info["PORT"] = input(f"Database port (default: '{default_port}'): ")
        # leave port setting empty, if default value is supplied and
        # leave it to django
        if info["PORT"] == default_port:
            info["PORT"] = ""
        info["NAME"] = input("Database name: ")
        info["USER"] = input("Username: ")
        info["PASSWORD"] = getpass.getpass("Password: ")
        return info

    def _get_extension_list(self):
        """Ask the API to get the list of all extensions.

        We hardcode the API url here to avoid a loading of
        django's settings since they are not available yet...
        """
        url = "http://api.modoboa.org/"
        official_exts = ModoAPIClient(url).list_extensions()
        return [
            extension["name"]
            for extension in official_exts
            if not extension["deprecated"]
        ]

    def find_extra_settings(self, extensions):
        """Install one or more extensions.

        Return the list of extensions providing settings we must
        include in the final configuration.

        """
        extra_settings = []
        for extension in extensions:
            module = __import__(extension[1], locals(), globals(), [])
            basedir = os.path.dirname(module.__file__)
            if not os.path.exists(f"{basedir}/settings.py"):
                continue
            extra_settings.append(extension[1])
        return extra_settings

    def handle(self, parsed_args):
        django.setup()
        management.call_command("startproject", parsed_args.name, verbosity=False)
        path = f"{parsed_args.name}/{parsed_args.name}"
        sys.path.append(parsed_args.name)

        conn_tpl = Template(DBCONN_TPL)
        connections = {}
        if parsed_args.dburl:
            for dburl in parsed_args.dburl:
                conn_name, url = dburl.split(":", 1)
                info = dj_database_url.config(default=url)
                # In case the user fails to supply a valid database url,
                # fallback to manual mode
                if not info:
                    print("There was a problem with your database-url. \n")
                    info = self.ask_db_info(conn_name)
                # If we set this earlier, our fallback method will never
                # be triggered
                info["conn_name"] = conn_name
                connections[conn_name] = conn_tpl.render(Context(info))
        else:
            connections["default"] = conn_tpl.render(Context(self.ask_db_info()))

        if parsed_args.domain:
            allowed_host = parsed_args.domain
        else:
            allowed_host = input("What will be the hostname used to access Modoboa? ")
            if not allowed_host:
                allowed_host = "localhost"
        extra_settings = []
        extensions = parsed_args.extensions
        if extensions:
            if "all" in extensions:
                extensions = self._get_extension_list()
            extensions = [
                (extension, extension.replace("-", "_")) for extension in extensions
            ]
            if not parsed_args.dont_install_extensions:
                cmd = (
                    sys.executable
                    + " -m pip install "
                    + " ".join([extension[0] for extension in extensions])
                )
                exec_cmd(cmd, capture_output=False)
            extra_settings = self.find_extra_settings(extensions)
            extensions = [extension[1] for extension in extensions]

        mod = __import__(parsed_args.name, globals(), locals(), [smart_str("settings")])
        tpl = self._render_template(
            f"{self._templates_dir}/settings.py.tpl",
            {
                "db_connections": connections,
                "secret_key": management.utils.get_random_secret_key(),
                "name": parsed_args.name,
                "allowed_host": allowed_host,
                "lang": parsed_args.lang,
                "timezone": parsed_args.timezone,
                "devmode": parsed_args.devel,
                "extensions": extensions,
                "extra_settings": extra_settings,
            },
        )
        with open(f"{path}/settings.py", "w") as fp:
            fp.write(tpl)
        generate_rsa_private_key(parsed_args.name)

        shutil.copyfile(f"{self._templates_dir}/urls.py.tpl", f"{path}/urls.py")
        os.mkdir(f"{parsed_args.name}/media")

        if isfile(f"{path}/settings.pyc"):
            os.unlink(f"{path}/settings.pyc")
        self._exec_django_command("migrate", parsed_args.name, "--noinput")
        self._exec_django_command(
            "load_initial_data",
            parsed_args.name,
            "--admin-username",
            parsed_args.admin_username,
        )
        if parsed_args.collectstatic:
            self._exec_django_command("collectstatic", parsed_args.name, "--noinput")
        self._exec_django_command("set_default_site", parsed_args.name, allowed_host)
