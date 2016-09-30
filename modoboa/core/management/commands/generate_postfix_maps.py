"""Management command to generate/update postfix map files."""

import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.utils import timezone

import dj_database_url

from ... import signals

MAP_FILE_TEMPLATE = """# This file was generated on {{ date }} by running:
# {{ commandline }}
# DO NOT EDIT!
"""


class Command(BaseCommand):
    """Command class."""

    help = "Generate/update postfix map files."

    def add_arguments(self, parser):
        """Add extra arguments."""
        parser.add_argument(
            "--dburl", help="Custom database url")
        parser.add_argument(
            "--destdir", default=".",
            help="Directory where files will be created")

    def __register_map_files(self):
        """Load specified applications."""
        responses = signals.register_postfix_maps.send(sender=self.__class__)
        mapfiles = []
        for response in responses:
            mapfiles += response[1]
        return mapfiles

    def get_template(self, dbtype):
        """Return map file template."""
        tplcontent = MAP_FILE_TEMPLATE
        if dbtype == "sqlite":
            tplcontent += """dbpath = {{ dbname }}
query = {{ query|safe }}
"""
        else:
            tplcontent += """user = {{ dbuser }}
password = {{ dbpass }}
dbname = {{ dbname }}
hosts = {{ dbhost }}
query = {{ query|safe }}
"""
        return Template(tplcontent)

    def get_template_context(self, options):
        """Build the context used to render templates."""
        dburl = options.get("dburl")
        db_settings = (
            dj_database_url.config(default=dburl)
            if dburl else settings.DATABASES["default"])
        if "sqlite" in db_settings["ENGINE"]:
            dbtype = "sqlite"
        elif "psycopg2" in db_settings["ENGINE"]:
            dbtype = "postgres"
        else:
            dbtype = "mysql"
        commandline = "{} {}".format(
            os.path.basename(sys.argv[0]), " ".join(sys.argv[1:]))
        context = {
            "date": timezone.now(),
            "commandline": commandline,
            "dbtype": dbtype,
            "dbuser": db_settings["USER"],
            "dbpass": db_settings["PASSWORD"],
            "dbname": db_settings["NAME"],
            "dbhost": db_settings.get("HOST", "127.0.0.1"),
        }
        return context

    def __render_map_file(self, mapobject, destdir, context):
        """Render a map file."""
        content = self.get_template(context["dbtype"]).render(
            Context(
                dict(context.items(),
                     query=getattr(mapobject, context["dbtype"]))
            )
        )
        fullpath = os.path.join(destdir, mapobject.filename)
        with open(fullpath, "w") as fp:
            fp.write("{}\n".format(content))

    def handle(self, *args, **options):
        """Command entry point."""
        mapfiles = self.__register_map_files()
        destdir = os.path.realpath(options["destdir"])
        try:
            os.mkdir(destdir)
        except OSError:
            pass
        context = self.get_template_context(options)
        for mapobject in mapfiles:
            self.__render_map_file(mapobject, destdir, context)
