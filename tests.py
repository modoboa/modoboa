# coding: utf-8
from __future__ import unicode_literals

import os
import tempfile
import unittest

from modoboa.lib.sysutils import exec_cmd

DB = os.environ.get("DB", "postgres")


class DeployTest(unittest.TestCase):
    dbtype = DB.lower()
    dbhost = "localhost"
    projname = "modoboa_test"
    dbuser = DB == "MYSQL" and "modoboa" or "postgres"
    dbpassword = DB == "MYSQL" and "modoboa" or ""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def test_silent(self):
        dburl = "default:%s://%s:%s@%s/%s" \
            % (self.dbtype, self.dbuser, self.dbpassword,
               self.dbhost, self.projname)
        cmd = (
            "modoboa-admin.py deploy --collectstatic "
            "--dburl %s --domain %s --admin-username admin %s"
            % (dburl, "localhost", self.projname)
        )
        code, output = exec_cmd(cmd, cwd=self.workdir)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
