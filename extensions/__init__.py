# -*- coding: utf-8 -*-
import os
import re
from django.conf import settings

def isinstalled(ext):
    return "modoboa.extensions.%s" % ext in settings.INSTALLED_APPS

def get_extension_infos(name):
    ext = __import__(name, globals(), locals(), ["main"])
    return ext.main.infos()

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
        module = __import__(f, globals(), locals(), ['main'])
        try:
            ext = Extension.objects.get(name=f)
            if ext.enabled:
                module.main.init()
        except Extension.DoesNotExist:
            pass
   	u = module.main.urls(prefix)
        if u == ():
            continue
        result += [u] 
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
        for f in ['urls.py', 'main.py', '__init__.py', 'views.py']:
            if not os.path.exists("%s/%s/%s" % (basedir, d, f)):
                isvalid = False
                break
        if isvalid:
            module = __import__(d, globals(), locals(), ['main'])
            try:
                infos = module.main.infos()
                infos["id"] = d
                if os.path.isdir("%s/%s/templates" % (basedir, d)):
                    infos["templates"] = True
                else:
                    infos["templates"] = False
                result += [infos]
            except AttributeError:
                pass
    return result

def loadmenus():
    result = []
    for name, mod in extensions.iteritems():
        u = mod.main.urls()
        if u == ():
            continue
        result += (u,)
    return result
