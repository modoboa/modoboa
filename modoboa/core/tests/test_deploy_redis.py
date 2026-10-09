"""Tests for the deploy command (Redis URL handling, see #3681)."""

import os

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

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "commands",
    "templates",
    "settings.py.tpl",
)


def _base_context():
    """Minimal context the settings template needs to render."""
    return {
        "db_connections": {},
        "secret_key": "dummy-secret-key",
        "redis_url": None,
        "name": "testinstance",
        "allowed_host": "localhost",
        "lang": "en",
        "timezone": "UTC",
        "devmode": False,
        "extensions": [],
        "extra_settings": [],
        "amavis_enabled": False,
        "server_domain": None,
    }


def render_settings(redis_url):
    """Render settings.py.tpl the way DeployCommand.handle() does."""
    with open(TEMPLATE_PATH) as fp:
        tpl = Template(fp.read())
    context = _base_context()
    context["redis_url"] = redis_url
    return tpl.render(Context(context))


def get_redis_url_line(rendered):
    """Return the REDIS_URL assignment line of a rendered settings.py."""
    for line in rendered.splitlines():
        stripped = line.strip()
        if stripped.startswith("REDIS_URL ="):
            return stripped
    raise AssertionError("No REDIS_URL line found in rendered settings")


class DeployRedisUrlTestCase(SimpleTestCase):
    """--redisurl must reach settings.py; the default must not change (#3681)."""

    def test_default_redis_url_is_unchanged(self):
        """Without --redisurl, REDIS_URL keeps its historical value."""
        line = get_redis_url_line(render_settings(None))
        self.assertEqual(
            line,
            "REDIS_URL = 'redis://{}:{}/{}'.format(REDIS_HOST, REDIS_PORT, "
            "REDIS_QUOTA_DB)",
        )

    def test_redisurl_overrides_redis_url(self):
        """A unix-socket URL passed via --redisurl must be rendered."""
        line = get_redis_url_line(
            render_settings("unix:///var/run/redis/redis.sock?db=0")
        )
        self.assertEqual(
            line, "REDIS_URL = 'unix:///var/run/redis/redis.sock?db=0'"
        )

    def test_tcp_redis_url_also_works(self):
        """A TCP URL on a non-default host/port must be rendered as-is."""
        line = get_redis_url_line(render_settings("redis://redis:6380/1"))
        self.assertEqual(line, "REDIS_URL = 'redis://redis:6380/1'")
