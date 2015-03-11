"""Tools for top level testing (ie. when ran by Travis)."""

import os
import tempfile

from .sysutils import exec_cmd


class TestRunnerMixin(object):

    """A test runner for extensions (travis only)."""

    dbtype = "postgres"
    dbhost = "localhost"
    projname = "modoboa_test"
    dbuser = "postgres"
    dbpassword = ""

    def setUp(self):
        """Test setup."""
        self.workdir = tempfile.mkdtemp()

    def test(self):
        """Run extensions tests."""
        dburl = "default:{0}://{1}:{2}@{3}/{4}".format(
            self.dbtype, self.dbuser, self.dbpassword, self.dbhost,
            self.projname
        )
        cmd = (
            "modoboa-admin.py deploy --collectstatic "
            "--dburl {0} --extensions {1} --dont-install-extensions "
            "--domain {2} {3}"
            .format(dburl, self.extension, "localhost", self.projname)
        )
        code, output = exec_cmd(cmd, cwd=self.workdir)
        self.assertEqual(code, 0)

        path = os.path.join(self.workdir, self.projname)
        cmd = "python manage.py test {0}.tests".format(self.extension)
        code, output = exec_cmd(cmd, capture_output=False, cwd=path)
        self.assertEqual(code, 0)


