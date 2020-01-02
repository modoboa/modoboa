"""Test map files generation."""

import os

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from modoboa.core.utils import parse_map_file
from modoboa.lib.test_utils import MapFilesTestCaseMixin


class MapFilesTestCase(MapFilesTestCaseMixin, TestCase):

    """Test case for admin."""

    MAP_FILES = [
        "sql-domains.cf", "sql-domain-aliases.cf", "sql-aliases.cf",
        "sql-maintain.cf", "sql-sender-login-map.cf"
    ]

    def test_map_upgrade(self):
        """Check that map content is used."""
        dburl = "postgres://user:password@localhost/testdb"
        call_command(
            "generate_postfix_maps",
            "--dburl", dburl, "--destdir", self.workdir)

        # Now upgrade files. Map credentials should be preserved.
        call_command("generate_postfix_maps", "--destdir", self.workdir)
        for f in self.MAP_FILES:
            mapcontent = parse_map_file(os.path.join(self.workdir, f))
            self.assertEqual(mapcontent["user"], "user")
            self.assertEqual(mapcontent["password"], "password")
            self.assertEqual(mapcontent["dbname"], "testdb")

        # Now force overwrite, credentials should be different
        call_command(
            "generate_postfix_maps", "--destdir", self.workdir,
            "--force-overwrite")
        dbsettings = settings.DATABASES["default"]
        for f in self.MAP_FILES:
            mapcontent = parse_map_file(os.path.join(self.workdir, f))
            if dbsettings["ENGINE"] == "django.db.backends.sqlite3":
                self.assertEqual(mapcontent["dbpath"], dbsettings["NAME"])
            else:
                self.assertEqual(mapcontent["user"], dbsettings["USER"])
                self.assertEqual(
                    mapcontent["password"], dbsettings["PASSWORD"])
                self.assertEqual(mapcontent["dbname"], dbsettings["NAME"])

        # Now modify a file manually
        path = os.path.join(self.workdir, "sql-domains.cf")
        with open(path, "a") as fp:
            fp.write("pouet")
        call_command("generate_postfix_maps", "--destdir", self.workdir)
        with open(path) as fp:
            content = fp.read()
        self.assertIn("pouet", content)
