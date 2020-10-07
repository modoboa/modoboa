"""Extensions management related test cases."""

import os
import sys
from io import StringIO

from testfixtures import compare

from django.core import management
from django.test import TestCase, override_settings

from modoboa.admin.models import Domain
from .. import extensions, signals

sys.path.append(os.path.dirname(__file__))

CUSTOM_APPS = (
    "modoboa",
    "modoboa.core",
    "modoboa.lib",
    "modoboa.admin",
    "modoboa.limits",
    "modoboa.relaydomains",
    "stupid_extension_1",
    "stupid_extension_2",
)


class ExtensionTestCase(TestCase):
    """Extensions related tests."""

    @classmethod
    def setUpClass(cls):
        """Initiate test context."""
        cls.pool = extensions.exts_pool
        with override_settings(MODOBOA_APPS=CUSTOM_APPS):
            cls.pool.load_all()

    @classmethod
    def tearDownClass(cls):
        """Reset context."""
        del cls.pool.extensions["stupid_extension_1"]
        del cls.pool.extensions["stupid_extension_2"]

    def test_register(self):
        """Test if registering works."""
        self.assertIn("stupid_extension_1", self.pool.extensions)

    def test_get_extension(self):
        """Check getter method."""
        self.assertIsNone(self.pool.get_extension("toto"))
        instance = self.pool.get_extension("stupid_extension_1")
        self.assertEqual(instance.__class__.__name__, "StupidExtension1")

    def test_get_extension_infos(self):
        """Check getter method."""
        self.assertIsNone(self.pool.get_extension_infos("toto"))
        infos = self.pool.get_extension_infos("stupid_extension_1")
        compare(infos, {
            "name": "stupid_extension_1", "label": "Stupid extension",
            "version": "1.0.0", "description": "A stupid extension",
            "url": "stupid_extension_1", "always_active": False,
            "topredirection_url": None
        })

    def test_list_all(self):
        """Check list_all method."""
        result = self.pool.list_all()
        self.assertEqual(len(result), 1)
        ext = result[0]
        self.assertEqual(ext["id"], "stupid_extension_1")

    def test_load_initial_data(self):
        """Check if method is called."""
        self.signal_called = 0

        def handler(sender, extname, **kwargs):
            self.assertEqual(extname, "stupid_extension_1")
            self.signal_called += 1

        signals.initial_data_loaded.connect(handler)

        stderr_out = StringIO()
        management.call_command("load_initial_data", stderr=stderr_out)
        self.assertTrue(Domain.objects.filter(name="stupid_1.com").exists())
        self.assertIn("stupid_extension_2", stderr_out.getvalue())
        self.assertEqual(self.signal_called, 1)

        signals.initial_data_loaded.disconnect(handler)

    def test_get_urls(self):
        """Load extensions urls."""
        urls = self.pool.get_urls()
        self.assertEqual(len(urls), 1)

        urls = self.pool.get_urls(category="api")
        self.assertEqual(len(urls), 0)
