"""Tools for top level testing (ie. when ran by Travis)."""

import os
import tempfile

from .sysutils import exec_cmd


class MapFilesTestCaseMixin(object):

    """A generic test case to check map files generation."""

    MAP_FILES = None

    extension = None

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        exec_cmd("rm -rf {0}".format(self.workdir))

    def _test_maps_generation(self, engine):
        dburl = "{0}://user:password@localhost/testdb".format(engine)
        code, output = exec_cmd(
            "modoboa-admin.py postfix_maps {0}--dburl {1} {2}".format(
                "--extensions {} ".format(self.extension)
                if self.extension else "", dburl, self.workdir
            )
        )
        self.assertEqual(code, 0)

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
