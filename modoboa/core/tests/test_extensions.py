"""Extensions management related test cases."""

import os
import sys

from testfixtures import compare

from django.core import management
from django.test import TestCase, override_settings

from .. import extensions

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

sys.path.append(os.path.dirname(__file__))


class StupidExtension2(extensions.ModoExtension):
    """Stupid extension to use with tests."""

    name = "stupid_extension_2"
    label = "Stupid extension"
    version = "1.0.0"
    description = "A stupid extension"

    def load(self):
        pass

    def load_initial_data(self):
        pass


@override_settings(MODOBOA_APPS=CUSTOM_APPS)
class ExtensionTestCase(TestCase):
    """Extensions related tests."""

    def setUp(self):
        """Initiate test context."""
        self.pool = extensions.exts_pool
        self.pool.load_all()

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
            "url": None, "always_active": False
        })

    def test_list_all(self):
        """Check list_all method."""
        result = self.pool.list_all()
        self.assertEqual(len(result), 1)
        ext = result[0]
        self.assertEqual(ext["id"], "stupid_extension_1")

    def test_load_initial_data(self):
        """Check if method is called."""
        with self.assertRaises(RuntimeError):
            management.call_command("load_initial_data")
