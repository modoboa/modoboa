# coding: utf-8
import os, sys
import re
from django.conf import settings
from django.conf.urls.defaults import include

class ModoExtension(object):
    """Base extension class

    Each Modoboa extension must inherit from this class to be
    considered as valid.
    """
    name = None
    version = "0.1"
    description = ""
    url = None
    needs_media = False

    def infos(self):
        return dict(name=self.name, label=self.label, version=self.version,
                    description=self.description, url=self.url)

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

    def register_extension(self, ext):
        self.extensions[ext.name] = dict(cls=ext)

    def get_extension(self, name):
        if not self.extensions.has_key(name):
            return None
        if not self.extensions[name].has_key("instance"):
            self.extensions[name]["instance"] = self.extensions[name]["cls"]()
        return self.extensions[name]["instance"]

    def get_extension_infos(self, name):
        instance = self.get_extension(name)
        return instance.infos()

    def load_all(self):
        from modoboa.admin.models import Extension

        result = []
        for extname, extdef in self.extensions.iteritems():
            extinstance = self.get_extension(extname)
            try:
                ext = Extension.objects.get(name=extname)
                if ext is None:
                    continue
                if ext.enabled:
                    extinstance.load()
            except Extension.DoesNotExist:
                pass
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
            infos = extdef["instance"].infos()
            infos["id"] = extname
            result += [infos]
        return sorted(result, key=lambda i: i["name"])

exts_pool = ExtensionsPool()
