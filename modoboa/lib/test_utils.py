# -*- coding: utf-8 -*-

"""Tools for top level testing (ie. when ran by Travis)."""

from __future__ import unicode_literals

import os
import shutil
import tempfile

from django.core.management import call_command


class MapFilesTestCaseMixin(object):
    """A generic test case to check map files generation."""

    MAP_FILES = None

    extension = None

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def _test_maps_generation(self, engine):
        dburl = "{0}://user:password@localhost/testdb".format(engine)
        call_command(
            "generate_postfix_maps",
            "--dburl", dburl, "--destdir", self.workdir)

        for mapfile in self.MAP_FILES:
            path = "{0}/{1}".format(self.workdir, mapfile)
            self.assertTrue(os.path.exists(path))
            with open(path) as fpo:
                content = fpo.read()
            if engine != "sqlite":
                self.assertIn("user = user", content)
                self.assertIn("password = password", content)
                self.assertIn("dbname = testdb", content)
                self.assertIn("hosts = localhost", content)
            else:
                self.assertIn("dbpath = testdb", content)

    def test_postgres_maps(self):
        self._test_maps_generation("postgres")

    def test_mysql_maps(self):
        self._test_maps_generation("mysql")

    def test_sqlite_maps(self):
        self._test_maps_generation("sqlite")
