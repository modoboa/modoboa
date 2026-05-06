"""Extension management."""

from django.conf import settings
from django.templatetags.static import static
from django.urls import include
from django.urls import re_path
from django.utils.encoding import smart_str


class ModoExtension:
    """
    Base extension class.

    Each Modoboa extension must inherit from this class to be
    considered as valid.
    """

    name: str
    label: str
    version: str = "NA"
    description: str = ""
    needs_media: bool = False
    always_active: bool = False
    url: str | None = None
    topredirection_url: str | None = None
    frontend_menu_entries: list[dict] = []
    frontend_routes: list[dict] = []
    frontend_remote: dict | None = None
    frontend_ui_extensions: dict[str, list[dict]] = {}

    def get_available_apps(self) -> list:
        return []

    def get_url(self):
        """Return extension base url."""
        if self.url is None:
            return self.name
        return self.url

    def infos(self):
        """Information about this extension."""
        return {
            "name": self.name,
            "label": self.label,
            "version": self.version,
            "description": self.description,
            "url": self.get_url(),
            "topredirection_url": self.topredirection_url,
            "always_active": self.always_active,
        }

    def get_frontend_menu_entries(self) -> list[dict]:
        """Return menu entries this extension wants to expose to the frontend."""
        return list(self.frontend_menu_entries)

    def get_frontend_routes(self) -> list[dict]:
        """Return routes this extension wants to register in the frontend router."""
        return list(self.frontend_routes)

    def get_frontend_remote(self) -> dict | None:
        """Return the federated remote descriptor for this extension, if any.

        Plugins may declare ``frontend_remote`` with either:

        - ``url``: an absolute or pre-resolved URL (used verbatim, e.g. CDN or
          dev server URL).
        - ``static_path``: a path relative to ``STATIC_URL``. The host resolves
          it through Django's ``static()`` helper so it picks up the configured
          ``STATIC_URL`` prefix and any hashed filename produced by
          ``ManifestStaticFilesStorage``.

        ``url`` takes precedence over ``static_path`` if both are set.
        """
        if not self.frontend_remote:
            return None
        remote = dict(self.frontend_remote)
        static_path = remote.pop("static_path", None)
        if not remote.get("url") and static_path:
            remote["url"] = static(static_path)
        return remote

    def get_frontend_ui_extensions(self) -> dict[str, list[dict]]:
        """Return UI extension descriptors keyed by extension-point id."""
        return {key: list(value) for key, value in self.frontend_ui_extensions.items()}

    def get_frontend_manifest(self) -> dict:
        """Return the frontend manifest of this extension."""
        return {
            "name": self.name,
            "label": self.label,
            "remote": self.get_frontend_remote(),
            "menu_entries": self.get_frontend_menu_entries(),
            "routes": self.get_frontend_routes(),
            "ui_extensions": self.get_frontend_ui_extensions(),
        }

    def load_initial_data(self):
        """Declare extension data in this method."""
        pass

    def load(self):
        """Add extension loading tasks in this method."""
        pass


class ExtensionsPool:
    """The extensions manager"""

    def __init__(self) -> None:
        self.extensions: dict[str, dict] = {}

    def register_extension(self, ext: ModoExtension, show: bool = True) -> None:
        """Register an extension.

        :param ext: a class inheriting from ``Extension``
        :param show: list the extension or not
        """
        self.extensions[ext.name] = {"cls": ext, "show": show}

    def get_extension(self, name: str) -> ModoExtension | None:
        """Retrieve the current instance of an extension."""
        if name not in self.extensions:
            return None
        if "instance" not in self.extensions[name]:
            self.extensions[name]["instance"] = self.extensions[name]["cls"]()
        return self.extensions[name]["instance"]

    def get_extension_infos(self, name):
        """Return information about the specified extension."""
        instance = self.get_extension(name)
        if instance is None:
            return None
        return instance.infos()

    def load_extension(self, name):
        """Load a registered extension."""
        __import__(name, locals(), globals(), [smart_str("modo_extension")])
        extinstance = self.get_extension(name)
        if extinstance is None:
            return None
        extinstance.load()
        return extinstance

    def load_all(self):
        """Load all defined extensions.

        Each extension must be loaded in order to integrate with
        Modoboa. Only enabled and special extensions are loaded but
        urls are always returned. The reason is urls are imported only
        once so must know all of them when the python process
        starts. Otherwise, it would lead to unexpected 404 errors :p

        :return: a list of url maps
        """
        for ext in settings.MODOBOA_APPS:
            self.load_extension(ext)

    def get_available_apps(self) -> list:
        result: list = []
        for ext_name in list(self.extensions.keys()):
            ext = self.get_extension(ext_name)
            if ext:
                result += ext.get_available_apps()
        return result

    def get_urls(self, category="app"):
        """Get all urls defined by extensions."""
        result = []
        for ext_name in list(self.extensions.keys()):
            ext = self.get_extension(ext_name)
            if category == "api":
                root = ""
                pattern = "{}.urls_api"
            else:
                root = rf"^{ext.get_url()}/"
                pattern = "{}.urls"
            try:
                result.append(re_path(root, include(pattern.format(ext_name))))
            except ImportError:
                # No urls for this extension
                pass
        return result

    def get_frontend_manifests(self) -> list[dict]:
        """Return frontend manifests of all registered extensions."""
        manifests = []
        for ext_name in list(self.extensions.keys()):
            ext = self.get_extension(ext_name)
            if ext is None:
                continue
            manifests.append(ext.get_frontend_manifest())
        return manifests

    def list_all(self):
        """List all defined extensions."""
        result = []
        for extname, extdef in list(self.extensions.items()):
            if not extdef["show"]:
                continue
            infos = self.get_extension_infos(extname)
            infos["id"] = extname
            result += [infos]
        return sorted(result, key=lambda i: i["name"])


exts_pool = ExtensionsPool()
