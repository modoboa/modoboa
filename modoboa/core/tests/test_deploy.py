"""Tests for the deploy command (database OPTIONS handling, see #1835)."""

import ast
import sys
import types

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        TEMPLATES=[
            {"BACKEND": "django.template.backends.django.DjangoTemplates"}
        ]
    )
    django.setup()

from django.template import Context, Template  # NOQA:E402
from django.test import SimpleTestCase  # NOQA:E402


def _load_deploy_module():
    """Import modoboa.core.commands.deploy with heavy imports stubbed.

    deploy.py imports helpers (api client, rsa key generation, ...) that
    pull in most of the application. They are irrelevant here, so we stub
    them to keep this test runnable without a full environment.
    """
    mod_name = "modoboa.core.commands.deploy"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    stubs = {
        "modoboa.core.utils": {"generate_rsa_private_key": lambda *a, **k: None},
        "modoboa.lib.api_client": {
            "ModoAPIClient": type("ModoAPIClient", (), {})
        },
        "modoboa.lib.sysutils": {"exec_cmd": lambda *a, **k: ""},
    }
    for name, attrs in stubs.items():
        if name not in sys.modules:
            module = types.ModuleType(name)
            for attr_name, attr_value in attrs.items():
                setattr(module, attr_name, attr_value)
            sys.modules[name] = module
    from modoboa.core.commands import deploy

    return deploy


deploy = _load_deploy_module()


def render_connection(info):
    """Simulate what DeployCommand.handle() does for one connection."""
    cmd = deploy.DeployCommand({})
    info = dict(info)
    info["OPTIONS"] = cmd._get_db_options(info)
    return Template(deploy.DBCONN_TPL).render(Context(info))


def parse_rendered_options(rendered):
    """Extract the DATABASES entry from a rendered snippet and return it."""
    tree = ast.parse("{" + rendered.strip().rstrip(",") + "}")
    return ast.literal_eval(tree.body[0].value)


class DeployDBOptionsTestCase(SimpleTestCase):
    """Database OPTIONS must survive deploy.py into settings.py (#1835)."""

    def test_mysql_ssl_options_from_dburl_are_kept(self):
        """SSL options parsed from --dburl must be rendered."""
        rendered = render_connection(
            {
                "conn_name": "default",
                "ENGINE": "django.db.backends.mysql",
                "NAME": "modoboa",
                "USER": "modoboa",
                "PASSWORD": "secret",
                "HOST": "db.example.com",
                "PORT": "3306",
                # what dj_database_url returns for
                # mysql://...?ssl-ca=/ca.pem&ssl-cert=/c.pem&ssl-key=/k.pem
                "OPTIONS": {
                    "ssl": {"ca": "/ca.pem"},
                    "ssl-cert": "/c.pem",
                    "ssl-key": "/k.pem",
                },
            }
        )
        self.assertNotIn("&#x27;", rendered)
        entry = parse_rendered_options(rendered)
        options = entry["default"]["OPTIONS"]
        self.assertEqual(
            options["ssl"], {"ca": "/ca.pem"}
        )
        self.assertEqual(options["ssl-cert"], "/c.pem")
        # historical default must still be there
        self.assertEqual(
            options["init_command"], "SET foreign_key_checks = 0;"
        )

    def test_mysql_keeps_default_init_command(self):
        """Plain mysql dburl still gets the historical init_command."""
        rendered = render_connection(
            {
                "conn_name": "default",
                "ENGINE": "django.db.backends.mysql",
                "NAME": "modoboa",
                "USER": "modoboa",
                "PASSWORD": "secret",
                "HOST": "localhost",
                "PORT": "",
            }
        )
        entry = parse_rendered_options(rendered)
        self.assertEqual(
            entry["default"]["OPTIONS"],
            {"init_command": "SET foreign_key_checks = 0;"},
        )

    def test_user_init_command_wins_over_default(self):
        """An explicit init_command from the dburl is not overridden."""
        rendered = render_connection(
            {
                "conn_name": "default",
                "ENGINE": "django.db.backends.mysql",
                "NAME": "modoboa",
                "USER": "modoboa",
                "PASSWORD": "secret",
                "HOST": "localhost",
                "PORT": "",
                "OPTIONS": {"init_command": "SET SESSION sql_mode='STRICT_ALL_TABLES'"},
            }
        )
        entry = parse_rendered_options(rendered)
        self.assertEqual(
            entry["default"]["OPTIONS"],
            {"init_command": "SET SESSION sql_mode='STRICT_ALL_TABLES'"},
        )

    def test_postgres_sslmode_is_rendered(self):
        """Postgres sslmode must be rendered, without mysql defaults."""
        rendered = render_connection(
            {
                "conn_name": "default",
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "modoboa",
                "USER": "modoboa",
                "PASSWORD": "secret",
                "HOST": "db.example.com",
                "PORT": "5432",
                # what dj_database_url returns for
                # postgres://...?sslmode=verify-full
                "OPTIONS": {"sslmode": "verify-full"},
            }
        )
        entry = parse_rendered_options(rendered)
        self.assertEqual(entry["default"]["OPTIONS"], {"sslmode": "verify-full"})

    def test_no_options_means_no_options_key(self):
        """Connections without options (e.g. sqlite) render no OPTIONS."""
        rendered = render_connection(
            {
                "conn_name": "default",
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "default.db",
            }
        )
        entry = parse_rendered_options(rendered)
        self.assertNotIn("OPTIONS", entry["default"])
