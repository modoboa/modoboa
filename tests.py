import os
import tempfile
import unittest

from modoboa.lib.sysutils import exec_cmd

DB = os.environ.get("DB", "postgres")
if DB.lower() == "postgres":
    PORT = os.environ.get("POSTGRES_PORT", "5432")
    DB = "postgres"
else:
    PORT = os.environ.get("MYSQL_PORT", "3306")
    DB = "mysql"


class DeployTest(unittest.TestCase):
    dbtype = DB
    dbhost = "localhost"
    dbport = PORT
    projname = "modoboa_test"
    dbuser = DB == "mysql" and "modoboa" or "postgres"
    dbpassword = DB == "mysql" and "modoboa" or ""

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def test_silent(self):
        dburl = "default:%s://%s:%s@%s:%s/%s" \
            % (self.dbtype, self.dbuser, self.dbpassword,
               self.dbhost, self.dbport, self.projname)
        cmd = (
            "modoboa-admin.py deploy --collectstatic "
            "--dburl %s --domain %s --admin-username admin %s"
            % (dburl, "localhost", self.projname)
        )
        code, output = exec_cmd(cmd, cwd=self.workdir)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
