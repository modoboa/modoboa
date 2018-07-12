# -*- coding: utf-8 -*-

"""Management command to generate/update postfix map files."""

from __future__ import print_function, unicode_literals

import copy
import hashlib
import os
import sys

import dj_database_url

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.utils import timezone
from django.utils.encoding import force_bytes

from ... import signals, utils

MAP_FILE_TEMPLATE = """# This file was generated on {{ date }} by running:
# {{ commandline }}
# DO NOT EDIT!
"""


class Command(BaseCommand):
    """Command class."""

    help = "Generate/update postfix map files."  # NOQA:A003

    def add_arguments(self, parser):
        """Add extra arguments."""
        parser.add_argument(
            "--dburl", help="Custom database url")
        parser.add_argument(
            "--destdir", default=".",
            help="Directory where files will be created")
        parser.add_argument(
            "--force-overwrite", action="store_true", default=False,
            help="Force overwrite of existing map files")

    def __load_checksums(self, destdir):
        """Load existing checksums if possible."""
        self.__checksums_file = os.path.join(
            destdir, "modoboa-postfix-maps.chk")
        self.__checksums = {}
        if not os.path.exists(self.__checksums_file):
            return
        with open(self.__checksums_file) as fp:
            for line in fp:
                fname, dbtype, checksum = line.split(":")
                self.__checksums[fname.strip()] = {
                    "dbtype": dbtype, "checksum": checksum.strip()
                }

    def __register_map_files(self):
        """Load specified applications."""
        responses = signals.register_postfix_maps.send(sender=self.__class__)
        mapfiles = []
        for response in responses:
            mapfiles += response[1]
        return mapfiles

    def __check_file(self, path):
        """Check if map file has been modified."""
        fname = os.path.basename(path)
        condition = (
            not self.__checksums or
            fname not in self.__checksums)
        if condition:
            return True
        with open(path, mode="rb") as fp:
            checksum = hashlib.md5(fp.read()).hexdigest()
        return checksum == self.__checksums[fname]["checksum"]

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
        elif "postgresql" in db_settings["ENGINE"]:
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

    def __render_map_file(
            self, mapobject, destdir, context, force_overwrite=False):
        """Render a map file."""
        fullpath = os.path.join(destdir, mapobject.filename)
        if os.path.exists(fullpath) and not force_overwrite:
            if not self.__check_file(fullpath):
                print(
                    "Cannot upgrade '{}' map because it has been modified."
                    .format(mapobject.filename))
                return self.__checksums[mapobject.filename]
            mapcontent = utils.parse_map_file(fullpath)
            context = copy.deepcopy(context)
            context["dbtype"] = self.__checksums[mapobject.filename]["dbtype"]
            if context["dbtype"] == "sqlite":
                context["dbname"] = mapcontent["dbpath"]
            else:
                context["dbuser"] = mapcontent["user"]
                context["dbpass"] = mapcontent["password"]
                context["dbname"] = mapcontent["dbname"]
                context["dbhost"] = mapcontent["hosts"]
        content = self.get_template(context["dbtype"]).render(
            Context(
                dict(list(context.items()),
                     query=getattr(mapobject, context["dbtype"]))
            )
        )
        fullpath = os.path.join(destdir, mapobject.filename)
        with open(fullpath, "w") as fp:
            fp.write(content)
        return hashlib.md5(force_bytes(content)).hexdigest()

    def handle(self, *args, **options):
        """Command entry point."""
        mapfiles = self.__register_map_files()
        destdir = os.path.realpath(options["destdir"])
        try:
            os.mkdir(destdir)
        except OSError:
            pass
        self.__load_checksums(destdir)
        context = self.get_template_context(options)
        checksums = {}
        for mapobject in mapfiles:
            checksum = self.__render_map_file(
                mapobject, destdir, context,
                force_overwrite=options["force_overwrite"])
            checksums[mapobject.filename] = checksum
        with open(self.__checksums_file, "w") as fp:
            for fname, checksum in list(checksums.items()):
                fp.write("{}:{}:{}\n".format(
                    fname, context["dbtype"], checksum))
