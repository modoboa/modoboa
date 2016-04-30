# coding: utf-8

"""postfix_maps command."""

import datetime
import getpass
import os
import sys

import django
from django.template import Context, Template

import dj_database_url

from . import Command

MAP_FILE_TEMPLATE = """user = {{ dbuser }}
password = {{ dbpass }}
dbname = {{ dbname }}
hosts = {{ dbhost }}
query = {{ query|safe }}
"""


class MapFilesRegistry(object):

    """A registry of all map files."""

    def __init__(self):
        self.files = []

    def add_files(self, files):
        """Add map files to registry."""
        self.files += files


registry = MapFilesRegistry()


class MapFilesGenerator(object):

    """Map files generator."""

    def __init__(self, dbinfo=None):
        """Constructor."""
        self.template = Template(MAP_FILE_TEMPLATE)
        if dbinfo is None:
            self.tpl_context = {
                'dbhost': raw_input('Database host: '),
                'dbname': raw_input('Database name: '),
                'dbuser': raw_input('Username: '),
                'dbpass': getpass.getpass('Password: ')
            }
        else:
            self.tpl_context = {
                'dbhost': dbinfo['HOST'],
                'dbname': dbinfo['NAME'],
                'dbuser': dbinfo['USER'],
                'dbpass': dbinfo['PASSWORD']
            }
        if not self.tpl_context['dbhost']:
            self.tpl_context['dbhost'] = '127.0.0.1'

    def __render_map(self, args, mapobject):
        """Render a map file.

        :param args: command line arguments
        :param mapobject: a ``MapFile`` subclass
        """
        content = self.template.render(
            Context(dict(
                self.tpl_context.items(),
                query=getattr(mapobject, args.dbtype)
            ))
        )
        with open("%s/%s" % (args.destdir, mapobject.filename), "w") as fp:
            fp.write("""# This file was generated on {} by running:
# {} {}
# DO NOT EDIT!
"""
                     .format(datetime.datetime.now().isoformat(),
                             os.path.basename(sys.argv[0]),
                             ' '.join(sys.argv[1:])))
            fp.write("{}\n".format(content))

    def __load_applications(self, applications):
        """Load specified applications."""
        for app in applications:
            extension = app.replace("-", "_")
            try:
                __import__(extension, locals(), globals(), ["postfix_maps"])
            except ImportError:
                sys.stderr.write("Unknown application {0}".format(extension))

    def render(self, args):
        """Render all map files.

        :param args: arguments received from the command line
        """
        try:
            os.mkdir(args.destdir)
        except OSError:
            pass
        applications = ["modoboa.admin", "modoboa.relaydomains"]
        if args.extensions:
            if "all" in applications:
                from modoboa.lib.api_client import ModoAPIClient

                # Retrieve extension list from the API
                url = "http://api.modoboa.org/"
                official_exts = ModoAPIClient(url).list_extensions()
                extensions = [
                    extension["name"] for extension in official_exts]
            else:
                extensions = args.extensions
            applications += extensions
        self.__load_applications(applications)
        for mapfile in registry.files:
            self.__render_map(args, mapfile)


class SQLiteMapFilesGenerator(MapFilesGenerator):

    """SQLite special generator."""

    def __init__(self, dbinfo=None):
        self.template = Template("""dbpath = {{ dbpath }}
query = {{ query|safe }}
""")
        if dbinfo is None:
            self.tpl_context = {
                'dbpath': raw_input('Database path: ')
            }
        else:
            self.tpl_context = {
                'dbpath': dbinfo['NAME']
            }


class PostfixMapsCommand(Command):

    """Base command to generate map files."""

    help = "Generate ready-to-use postfix map files"

    def __init__(self, *args, **kwargs):
        super(PostfixMapsCommand, self).__init__(*args, **kwargs)
        self._parser.add_argument(
            'destdir', type=str,
            help='Directory that will contain generated map files'
        )
        self._parser.add_argument(
            '--dbtype', type=str, choices=['mysql', 'postgres', 'sqlite'],
            default='mysql',
            help='Used database type'
        )
        self._parser.add_argument(
            '--dburl', type=str, nargs=1, default=None,
            help="url of Modoboa's database"
        )
        self._parser.add_argument(
            '--extensions', type=str, nargs='+',
            help=(
                'Generate map files for this extensions '
                '("all" shortcut available)'
            )
        )

    def handle(self, parsed_args):
        """Command entry point."""
        django.setup()
        dbinfo = None
        if parsed_args.dburl:
            dbinfo = dj_database_url.config(default=parsed_args.dburl[0])
            if 'sqlite' in dbinfo['ENGINE']:
                parsed_args.dbtype = 'sqlite'
            elif 'psycopg2' in dbinfo['ENGINE']:
                parsed_args.dbtype = 'postgres'
            else:
                parsed_args.dbtype = 'mysql'
        if parsed_args.dbtype == 'sqlite':
            generator = SQLiteMapFilesGenerator(dbinfo)
        else:
            generator = MapFilesGenerator(dbinfo)
        generator.render(parsed_args)
