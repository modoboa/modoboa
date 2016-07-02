"""Extension management."""

from django.conf import settings
from django.conf.urls import include


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

    def load_extension(self, name):
        """Load a registered extension."""
        __import__(name, locals(), globals(), ["modo_extension"])
        extinstance = self.get_extension(name)
        if extinstance is None:
            return None
        result = None
        try:
            baseurl = (
                extinstance.url if extinstance.url is not None
                else name
            )
            result = (
                r'^%s/' % (baseurl),
                include("{0}.urls".format(name), namespace=name)
            )
        except ImportError:
            # No urls for this extension
            pass
        extinstance.load()
        return result

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
            ext_urls = self.load_extension(ext)
            if ext_urls is not None:
                result += [ext_urls]
        return result

    def list_all(self):
        """List all defined extensions."""
        result = []
        for extname, extdef in self.extensions.iteritems():
            if not extdef["show"]:
                continue
            infos = self.get_extension_infos(extname)
            infos["id"] = extname
            result += [infos]
        return sorted(result, key=lambda i: i["name"])

exts_pool = ExtensionsPool()
