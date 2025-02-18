"""modoboa-stats tests."""

import datetime
import os
import shutil
import tempfile

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.test import override_settings

from modoboa.admin import factories as admin_factories
from modoboa.core import models as core_models
from modoboa.lib.tests import ModoTestCase


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
class ViewsTestCase(RunCommandsMixin, ModoTestCase):
    """Views test cases."""

    @classmethod
    def setUpTestData(cls):  # noqa
        super().setUpTestData()
        admin_factories.populate_database()
        cls.da = core_models.User.objects.get(username="admin@test.com")

    def tearDown(self):
        super().tearDown()
        self.set_global_parameter("greylist", False)

    def test_index(self):
        """Test index view."""
        url = reverse("maillog:fullindex")
        response = self.client.get(url)
        self.assertContains(response, 'id="graphs_accountgraphicset"')
        self.assertContains(response, 'id="graphs_mailtraffic"')

        self.client.force_login(self.da)
        response = self.client.get(url)
        self.assertContains(response, 'id="graphs_mailtraffic"')

    def test_graphs(self):
        """Test graphs views."""
        self.run_logparser()
        url = reverse("maillog:graph_list")
        self.ajax_get(url, status=404)
        response = self.ajax_get(f"{url}?gset=mailtraffic")
        self.assertIn("averagetraffic", response["graphs"])
        for period in ["week", "month", "year"]:
            response = self.ajax_get(f"{url}?gset=mailtraffic&period={period}")
            self.assertIn("averagetraffic", response["graphs"])
            self.assertEqual(response["period_name"], period)

        # custom period
        today = datetime.date.today()
        start = f"{today} 11:00:00"
        end = f"{today} 11:40:00"
        response = self.ajax_get(
            f"{url}?gset=mailtraffic&period=custom&start={start}&end={end}"
        )
        self.assertIn("averagetraffic", response["graphs"])

        # unknown domain
        response = self.ajax_get(
            f"{url}?gset=mailtraffic&searchquery=unknown.com", status=400
        )

        # check with greylist enabled
        self.set_global_parameter("greylist", True)
        response = self.ajax_get(f"{url}?gset=mailtraffic")
        self.assertIn("averagetraffic", response["graphs"])

    def test_account_created_graph(self):
        """Check data."""
        self.run_update_statistics(rebuild=True)
        url = reverse("maillog:graph_list")
        response = self.ajax_get(f"{url}?gset=accountgraphicset")
        data = response["graphs"]["accountcreationgraphic"]["series"][0]["data"]
        self.assertEqual(data[-1]["y"], 5.0)

    def test_graphs_as_domainadmin(self):
        """Test graph views as domain admin."""
        self.run_logparser()
        self.client.force_login(self.da)
        url = "{}?gset=mailtraffic".format(reverse("maillog:graph_list"))
        response = self.ajax_get(url)
        self.assertIn("averagetraffic", response["graphs"])

        response = self.ajax_get(f"{url}&searchquery=test.com")
        self.assertIn("averagetraffic", response["graphs"])

        response = self.ajax_get(f"{url}&searchquery=test2.com", status=403)

    def test_get_domain_list(self):
        """Test get_domain_list view."""
        url = reverse("maillog:domain_list")
        response = self.ajax_get(url)
        self.assertIn("test.com", response)
        self.assertIn("test2.com", response)


@override_settings(RRDTOOL_TEST_MODE=True)
class ManagementCommandsTestCase(RunCommandsMixin, ModoTestCase):
    """Management command test cases."""

    @classmethod
    def setUpTestData(cls):  # noqa
        super().setUpTestData()
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
