"""modoboa-stats tests."""

import datetime
import os
import shutil
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings

from modoboa.admin import factories as admin_factories
from modoboa.lib.tests import SimpleModoTestCase


class RunCommandsMixin:
    """Mixin to run management commands."""

    def setUp(self):
        super().setUp()
        self.workdir = tempfile.mkdtemp()
        self.set_global_parameter("rrd_rootdir", self.workdir)

    def tearDown(self):
        shutil.rmtree(self.workdir)
        pid_file = f"{settings.PID_FILE_STORAGE_PATH}/modoboa_logparser.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)

    def run_logparser(self):
        """Run logparser command."""
        path = os.path.join(os.path.dirname(__file__), "mail.log")
        with open(path) as fp:
            content = fp.read() % {"day": datetime.date.today().strftime("%b %d")}
        path = os.path.join(self.workdir, "mail.log")
        with open(path, "w") as fp:
            fp.write(content)
        self.set_global_parameter("logfile", path)
        call_command("logparser")

    def run_update_statistics(self, rebuild=False):
        """Run update_statistics command."""
        args = []
        if rebuild:
            args.append("--rebuild")
        call_command("update_statistics", *args)


@override_settings(RRDTOOL_TEST_MODE=True)
class ManagementCommandsTestCase(RunCommandsMixin, SimpleModoTestCase):
    """Management command test cases."""

    @classmethod
    def setUpTestData(cls):  # noqa
        super().setUpTestData()
        call_command("load_initial_data", "--no-frontend")
        admin_factories.populate_database()

    def test_logparser(self):
        """Test logparser command."""
        self.run_logparser()
        for d in ["global", "test.com"]:
            path = os.path.join(self.workdir, f"{d}.rrd")
            self.assertTrue(os.path.exists(path))

    def test_logparser_with_greylist(self):
        """Test logparser when greylist activated."""
        self.set_global_parameter("greylist", True)
        self.run_logparser()
        for d in ["global", "test.com"]:
            path = os.path.join(self.workdir, f"{d}.rrd")
            self.assertTrue(os.path.exists(path))

    def test_update_statistics(self):
        """Test update_statistics command."""
        self.run_update_statistics()
        path = os.path.join(self.workdir, "new_accounts.rrd")
        self.assertTrue(os.path.exists(path))
        self.run_update_statistics(rebuild=True)
        self.assertTrue(os.path.exists(path))

    def test_locking(self):
        with open(f"{settings.PID_FILE_STORAGE_PATH}/modoboa_logparser.pid", "w") as fp:
            fp.write(f"{os.getpid()}\n")
        with self.assertRaises(SystemExit) as inst:
            self.run_logparser()
        self.assertEqual(inst.exception.code, 2)
