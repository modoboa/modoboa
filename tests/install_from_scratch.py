# coding: utf-8

import os
import sys
import subprocess
import tempfile
import pexpect
import shutil
import unittest


def runcmd(cmd, **kwargs):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=True, **kwargs)
    output = p.communicate()[0]
    return p.returncode, output


class DeployTest(unittest.TestCase):
    dbtype = "mysql"
    dbhost = "localhost"
    projname = "modoboa_test"
    dbuser = "root"
    dbpassword = "toto"

    def setUp(self):
        cmd = "mysqladmin -u %s -p%s create %s" % (self.dbuser, self.dbpassword, self.projname)
        code, out = runcmd(cmd)
        self.assertEqual(code, 0)
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        if hasattr(self, "workdir"):
            shutil.rmtree(self.workdir)
        child = pexpect.spawn("mysqladmin -u root -p%s drop %s" % (self.dbpassword, self.projname))
        child.expect("\[y/N\]")
        child.sendline("y")
        child.expect('Database "%s" dropped' % self.projname)

    def test(self):
        timeout = 2
        cmd = "modoboa-admin.py deploy --syncdb --collectstatic %s" % self.projname
        child = pexpect.spawn(cmd, cwd=self.workdir)
        fout = open('install_from_scratch.log','w')
        child.logfile = fout
        child.expect("Database type \(mysql, postgres or sqlite3\):", timeout=timeout)
        child.sendline(self.dbtype)
        child.expect("Database host \(default: 'localhost'\):", timeout=timeout)
        child.sendline(self.dbhost)
        child.expect("Database name:", timeout=timeout)
        child.sendline(self.projname)
        child.expect("Username:", timeout=timeout)
        child.sendline(self.dbuser)
        child.expect("Password:", timeout=timeout)
        child.sendline(self.dbpassword)
        child.expect("Under which domain do you want to deploy modoboa?", timeout=timeout)
        child.sendline("localhost")
        child.wait()
        fout.close()
        self.assertEqual(child.exitstatus, 0)

        path = os.path.join(self.workdir, self.projname)
        code, output = runcmd("python manage.py test admin", cwd=path)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
