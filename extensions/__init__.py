# coding: utf-8
import os, sys
import re
from django.conf import settings
from django.conf.urls.defaults import include

def isinstalled(ext):
    return "modoboa.extensions.%s" % ext in settings.INSTALLED_APPS

def get_ext_module(extname):
    modname = "modoboa.extensions.%s" % extname
    if not sys.modules.has_key(modname):
        __import__(modname)
    return sys.modules[modname]

def get_extension_infos(name):
    return get_ext_module(name).infos()

def loadextensions(prefix):
    # To avoid a circular import...
    from modoboa.admin.models import Extension

    basedir = "%s/extensions" % settings.MODOBOA_DIR
    result = []
    for f in os.listdir(basedir):
	if not os.path.isdir("%s/%s" % (basedir, f)):
	    continue
	if not isinstalled(f):
	    continue
        try:
            ext = Extension.objects.get(name=f)
            if ext.enabled:
                ext.load()
        except Extension.DoesNotExist:
            pass
        module = get_ext_module(f)
        baseurl = module.baseurl if hasattr(module, "baseurl") \
            else f
        result += [(r'%s%s/' % (prefix, baseurl),
                    include("modoboa.extensions.%s.urls" % f))]
    return result

def list_extensions():
    basedir = "%s/extensions" % settings.MODOBOA_DIR
    result = []
    for d in os.listdir(basedir):
        if not os.path.isdir("%s/%s" % (basedir, d)):
            continue
        if not isinstalled(d):
            continue
        isvalid = True
        for f in ['urls.py', '__init__.py', 'views.py']:
            if not os.path.exists("%s/%s/%s" % (basedir, d, f)):
                isvalid = False
                break
        if isvalid:
            module = __import__(d, globals(), locals())
            try:
                infos = module.infos()
                infos["id"] = d
                if os.path.isdir("%s/%s/templates" % (basedir, d)):
                    infos["templates"] = True
                else:
                    infos["templates"] = False
                result += [infos]
            except AttributeError:
                pass
    return result
