import os
import tempfile

from django.core.urlresolvers import reverse
from django.test import TestCase

from modoboa.lib.sysutils import exec_cmd
from modoboa.lib.tests import ModoTestCase
from . import factories


class ProfileTestCase(ModoTestCase):
    fixtures = ['initial_users.json']

    def setUp(self):
        super(ProfileTestCase, self).setUp()
        self.account = factories.UserFactory(
            username="user@test.com", groups=('SimpleUsers',)
        )

    def test_update_password(self):
        """Password update

        Two cases:
        * The default admin changes his password (no associated Mailbox)
        * A normal user changes his password
        """
        self.ajax_post(reverse("core:user_profile"),
                       {"oldpassword": "password",
                        "newpassword": "titi", "confirmation": "titi"})
        self.clt.logout()

        self.assertEqual(
            self.clt.login(username="admin", password="titi"), True
        )
        self.assertEqual(
            self.clt.login(username="user@test.com", password="toto"), True
        )

        self.ajax_post(
            reverse("core:user_profile"),
            {"oldpassword": "toto",
             "newpassword": "tutu", "confirmation": "tutu"}
        )
        self.clt.logout()
        self.assertTrue(
            self.clt.login(username="user@test.com", password="tutu")
        )


class ModoboaAdminCommandTestCase(TestCase):
    MAP_FILES = {
        "std": [
            "sql-domains.cf", "sql-domain-aliases.cf", "sql-aliases.cf",
            "sql-domain-aliases-mailboxes.cf", "sql-catchall-aliases.cf",
            "sql-maintain.cf"
        ],
        "autoreply": ["sql-autoreplies-transport.cf", "sql-autoreplies.cf"],
        "relaydomains": [
            "sql-relaydomains.cf", "sql-relaydomains-transport.cf",
            "sql-relaydomain-aliases-transport.cf",
            "sql-relay-recipient-verification.cf"
        ]
    }

    def setUp(self):
        self.workdir = tempfile.mkdtemp()

    def tearDown(self):
        exec_cmd("rm -rf {0}".format(self.workdir))

    def _test_maps_generation(self, engine, categories=None):
        if categories is None:
            categories = ["std", "autoreply", "relaydomains"]
        dburl = "{0}://user:password@localhost/testdb".format(engine)
        code, output = exec_cmd(
            "modoboa-admin.py postfix_maps --categories {0} --dburl {1} {2}".format(
                " ".join(categories), dburl, self.workdir
            )
        )
        self.assertEqual(code, 0)
        for category in categories:
            for mapfile in self.MAP_FILES[category]:
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
