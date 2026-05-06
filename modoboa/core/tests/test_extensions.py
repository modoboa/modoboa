"""Extensions management related test cases."""

import os
import sys
from io import StringIO

from testfixtures import compare

from django.conf import settings
from django.core import management
from django.test import TestCase, override_settings
from django.urls import reverse

from modoboa.admin.models import Domain
from modoboa.lib.tests import ModoAPITestCase
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
        compare(
            infos,
            {
                "name": "stupid_extension_1",
                "label": "Stupid extension",
                "version": "1.0.0",
                "description": "A stupid extension",
                "url": "stupid_extension_1",
                "always_active": False,
                "topredirection_url": None,
            },
        )

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


class ModoExtensionFrontendManifestTests(TestCase):
    """Cover the frontend-manifest helpers added for the plugin system."""

    def _ext(self, **attrs):
        """Build a one-off ModoExtension subclass with the given overrides."""
        defaults = {"name": "ext", "label": "Ext"}
        defaults.update(attrs)
        return type("_Ext", (extensions.ModoExtension,), defaults)()

    def test_remote_url_passthrough(self):
        ext = self._ext(
            frontend_remote={
                "name": "x",
                "url": "https://cdn.example/x.js",
                "format": "esm",
            }
        )
        self.assertEqual(
            ext.get_frontend_remote(),
            {"name": "x", "url": "https://cdn.example/x.js", "format": "esm"},
        )

    def test_remote_static_path_resolved_via_static_url(self):
        ext = self._ext(
            frontend_remote={
                "name": "x",
                "static_path": "x/remoteEntry.js",
                "format": "esm",
            }
        )
        remote = ext.get_frontend_remote()
        # url comes from django's static() helper, which prefixes STATIC_URL.
        self.assertNotIn("static_path", remote)
        self.assertTrue(remote["url"].endswith("x/remoteEntry.js"))
        self.assertTrue(remote["url"].startswith(settings.STATIC_URL))
        self.assertEqual(remote["format"], "esm")

    def test_remote_url_takes_precedence_over_static_path(self):
        ext = self._ext(
            frontend_remote={
                "name": "x",
                "url": "https://cdn.example/x.js",
                "static_path": "x/remoteEntry.js",
            }
        )
        remote = ext.get_frontend_remote()
        self.assertEqual(remote["url"], "https://cdn.example/x.js")
        self.assertNotIn("static_path", remote)

    def test_remote_none_when_not_declared(self):
        self.assertIsNone(self._ext().get_frontend_remote())

    def test_get_frontend_manifest_aggregates_declarations(self):
        ext = self._ext(
            frontend_menu_entries=[{"label": "Foo", "to": "FooRoute"}],
            frontend_routes=[{"name": "FooRoute", "path": "foo", "component": "./Foo"}],
            frontend_ui_extensions={
                "domain.detail.tabs": [
                    {"name": "ext.tab", "title": "Tab", "component": "./Tab"}
                ]
            },
            frontend_remote={"name": "ext", "url": "https://cdn/x.js"},
        )
        manifest = ext.get_frontend_manifest()
        self.assertEqual(manifest["name"], "ext")
        self.assertEqual(manifest["label"], "Ext")
        self.assertEqual(manifest["remote"]["url"], "https://cdn/x.js")
        self.assertEqual(manifest["menu_entries"][0]["to"], "FooRoute")
        self.assertEqual(manifest["routes"][0]["component"], "./Foo")
        self.assertEqual(
            manifest["ui_extensions"]["domain.detail.tabs"][0]["component"],
            "./Tab",
        )

    def test_getters_return_independent_copies(self):
        """Mutating the returned list must not corrupt the class attribute."""
        original = [{"label": "X"}]
        ext = self._ext(frontend_menu_entries=original)
        out = ext.get_frontend_menu_entries()
        out.append({"label": "Y"})
        self.assertEqual(len(original), 1)


class ExtensionsPoolFrontendManifestsTests(TestCase):
    """``ExtensionsPool.get_frontend_manifests`` aggregation."""

    def setUp(self):
        super().setUp()
        self.pool = extensions.exts_pool

        class _AggExt(extensions.ModoExtension):
            name = "agg_test_ext"
            label = "Aggregation test"
            version = "1.0.0"
            description = "Used by ExtensionsPoolFrontendManifestsTests"
            frontend_menu_entries = [{"label": "Agg", "to": "AggRoute"}]

        self.pool.register_extension(_AggExt)
        self.addCleanup(self.pool.extensions.pop, "agg_test_ext", None)

    def test_manifest_per_registered_extension(self):
        manifests = self.pool.get_frontend_manifests()
        names = {m["name"] for m in manifests}
        self.assertIn("agg_test_ext", names)
        # Every manifest exposes the documented keys, regardless of which
        # extensions are registered alongside it.
        for manifest in manifests:
            self.assertIn("menu_entries", manifest)
            self.assertIn("routes", manifest)
            self.assertIn("ui_extensions", manifest)
            self.assertIn("remote", manifest)


class FrontendPluginsAPIViewTests(ModoAPITestCase):
    """``GET /api/v2/frontend/plugins/`` exposes the manifest list."""

    def setUp(self):
        super().setUp()

        class _PluginExt(extensions.ModoExtension):
            name = "test_plugin"
            label = "Test plugin"
            version = "1.0.0"
            description = "Plugin used by FrontendPluginsAPIViewTests"
            frontend_remote = {
                "name": "test_plugin",
                "url": "https://localhost:5174/remoteEntry.js",
                "format": "esm",
            }
            frontend_menu_entries = [
                {
                    "label": "Test plugin",
                    "icon": "mdi-test-tube",
                    "to": "TestPluginRoute",
                    "category": "admin",
                    "roles": ["SuperAdmins"],
                }
            ]
            frontend_routes = [
                {
                    "name": "TestPluginRoute",
                    "path": "test-plugin",
                    "component": "./TestPlugin",
                    "parent": "AdminLayout",
                }
            ]
            frontend_ui_extensions = {
                "domain.detail.tabs": [
                    {
                        "name": "test_plugin.tab",
                        "title": "Test tab",
                        "component": "./TestTab",
                    }
                ]
            }

        extensions.exts_pool.register_extension(_PluginExt)
        self.addCleanup(extensions.exts_pool.extensions.pop, "test_plugin", None)

    def test_requires_authentication(self):
        self.client.credentials()  # drop auth token from base setUp
        response = self.client.get(reverse("v2:frontend_plugins"))
        self.assertEqual(response.status_code, 401)

    def test_returns_manifests_for_registered_extensions(self):
        response = self.client.get(reverse("v2:frontend_plugins"))
        self.assertEqual(response.status_code, 200)
        manifests = {m["name"]: m for m in response.json()}
        self.assertIn("test_plugin", manifests)

        manifest = manifests["test_plugin"]
        self.assertEqual(manifest["label"], "Test plugin")
        self.assertEqual(
            manifest["remote"]["url"],
            "https://localhost:5174/remoteEntry.js",
        )
        self.assertEqual(manifest["menu_entries"][0]["to"], "TestPluginRoute")
        self.assertEqual(manifest["routes"][0]["component"], "./TestPlugin")
        self.assertEqual(
            manifest["ui_extensions"]["domain.detail.tabs"][0]["component"],
            "./TestTab",
        )

    def test_remote_static_path_is_resolved_in_manifest(self):
        ext = extensions.exts_pool.get_extension("test_plugin")
        ext.frontend_remote = {
            "name": "test_plugin",
            "static_path": "test_plugin/remoteEntry.js",
            "format": "esm",
        }
        response = self.client.get(reverse("v2:frontend_plugins"))
        self.assertEqual(response.status_code, 200)
        manifest = next(m for m in response.json() if m["name"] == "test_plugin")
        self.assertTrue(manifest["remote"]["url"].startswith(settings.STATIC_URL))
        self.assertTrue(
            manifest["remote"]["url"].endswith("test_plugin/remoteEntry.js")
        )
