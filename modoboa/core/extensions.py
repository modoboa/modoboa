import os
import sys
import re
from django.conf import settings
from django.conf.urls import include


class ModoExtension(object):
    """Base extension class

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

    def infos(self):
        return dict(
            name=self.name, label=self.label, version=self.version,
            description=self.description, url=self.url,
            always_active=self.always_active
        )

    def init(self):
        pass

    def destroy(self):
        pass

    def load(self):
        pass


class ExtensionsPool(object):
    """The extensions manager"""

    def __init__(self):
        self.extensions = dict()

    def register_extension(self, ext, show=True):
        self.extensions[ext.name] = dict(cls=ext, show=show)

    def get_extension(self, name):
        if not name in self.extensions:
            return None
        if not "instance" in self.extensions[name]:
            self.extensions[name]["instance"] = self.extensions[name]["cls"]()
        return self.extensions[name]["instance"]

    def get_extension_infos(self, name):
        instance = self.get_extension(name)
        if instance is None:
            return None
        return instance.infos()

    def load_all(self):
        from modoboa.core.models import Extension

        for ext in settings.MODOBOA_APPS:
            __import__(ext)
        result = []
        for extname in self.extensions.keys():
            extinstance = self.get_extension(extname)
            if not extinstance.always_active:
                try:
                    ext = Extension.objects.get(name=extname)
                    if not ext.enabled:
                        continue
                except Extension.DoesNotExist:
                    continue
            extinstance.load()
            try:
                baseurl = extinstance.url if extinstance.url is not None else extname
                result += [(r'^%s/' % (baseurl),
                            include("%s.urls" % extinstance.__module__))]
            except ImportError:
                # No urls for this extension
                pass
        return result

    def list_all(self):
        result = []
        for extname, extdef in self.extensions.iteritems():
            if not extdef["show"]:
                continue
            infos = extdef["instance"].infos()
            infos["id"] = extname
            result += [infos]
        return sorted(result, key=lambda i: i["name"])

exts_pool = ExtensionsPool()
