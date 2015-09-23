# coding: utf-8

import tempfile
import unittest

from modoboa.lib.sysutils import exec_cmd


class DeployTest(unittest.TestCase):
    dbtype = "postgres"
    dbhost = "localhost"
    projname = "modoboa_test"
    dbuser = "postgres"
    dbpassword = ""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def test_silent(self):
        dburl = "default:%s://%s:%s@%s/%s" \
            % (self.dbtype, self.dbuser, self.dbpassword,
               self.dbhost, self.projname)
        cmd = (
            "modoboa-admin.py deploy --collectstatic "
            "--dburl %s --domain %s %s"
            % (dburl, 'localhost', self.projname)
        )
        code, output = exec_cmd(cmd, cwd=self.workdir)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
