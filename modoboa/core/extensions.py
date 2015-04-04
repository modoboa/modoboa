"""Extension management."""

from django.conf import settings
from django.conf.urls import include

from versionfield.constants import DEFAULT_NUMBER_BITS
from versionfield.version import Version

from modoboa.lib.api_client import ModoAPIClient


class ModoExtension(object):

    """
    Base extension class.

    Each Modoboa extension must inherit from this class to be
    considered as valid.
    """

    name = None
    label = None
    version = "NA"
    description = ""
    url = None
    needs_media = False
    always_active = False
    available_for_topredirection = False

    def infos(self):
        return dict(
            name=self.name, label=self.label, version=self.version,
            description=self.description, url=self.url,
            always_active=self.always_active
        )

    def load_initial_data(self):
        """Declare extension data in this method."""
        pass

    def load(self):
        pass


class ExtensionsPool(object):

    """The extensions manager"""

    def __init__(self):
        self.extensions = {}

    def register_extension(self, ext, show=True):
        """Register an extension.

        :param ext: a class inheriting from ``Extension``
        :param show: list the extension or not
        """
        self.extensions[ext.name] = dict(cls=ext, show=show)

    def get_extension(self, name):
        """Retrieve the current instance of an extension."""
        if name not in self.extensions:
            return None
        if "instance" not in self.extensions[name]:
            self.extensions[name]["instance"] = self.extensions[name]["cls"]()
        return self.extensions[name]["instance"]

    def is_extension_installed(self, name):
        """Check if an extension is installed ir not."""
        return name in settings.MODOBOA_APPS

    def get_extension_infos(self, name):
        instance = self.get_extension(name)
        if instance is None:
            return None
        return instance.infos()

    def load_all(self):
        """Load all defined extensions.

        Each extension must be loaded in order to integrate with
        Modoboa. Only enabled and special extensions are loaded but
        urls are always returned. The reason is urls are imported only
        once so must know all of them when the python process
        starts. Otherwise, it would lead to unexpected 404 errors :p

        :return: a list of url maps
        """
        result = []
        for ext in settings.MODOBOA_APPS:
            __import__(ext, locals(), globals(), ["modo_extension"])
            extname = ext.split('.')[-1]
            extinstance = self.get_extension(extname)
            if extinstance is None:
                continue
            try:
                baseurl = extinstance.url \
                    if extinstance.url is not None else extname
                result += [
                    (r'^%s/' % (baseurl),
                     include("{0}.urls".format(ext), namespace=extname))
                ]
            except ImportError:
                # No urls for this extension
                pass
            extinstance.load()
        return result

    def list_all(self, check_new_versions=False):
        """List all defined extensions."""
        result = []
        if check_new_versions:
            new_extensions = ModoAPIClient().list_extensions()
            new_extensions = dict(
                (ext["name"], ext["version"]) for ext in new_extensions
            )
        else:
            new_extensions = {}
        for extname, extdef in self.extensions.iteritems():
            if not extdef["show"]:
                continue
            infos = self.get_extension_infos(extname)
            infos["id"] = extname
            local_version = Version(infos["version"], DEFAULT_NUMBER_BITS)
            pkgname = infos["name"].replace("_", "-")
            if pkgname in new_extensions:
                infos["last_version"] = new_extensions[pkgname]
                last_version = Version(
                    new_extensions[pkgname], DEFAULT_NUMBER_BITS)
                if last_version > local_version:
                    infos["update"] = True
            result += [infos]
        return sorted(result, key=lambda i: i["name"])

exts_pool = ExtensionsPool()
