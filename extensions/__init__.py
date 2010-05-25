# -*- coding: utf-8 -*-
import os
import re

extensions = {}

def loadextensions():
    from admin.models import Extension
    from django.template import add_to_builtins

    exts = Extension.objects.filter(enabled=True)
    for ext in exts:
        tagsdir = "extensions/%s/templatetags" % ext.name
        if os.path.isdir("extensions/%s/templatetags" % ext.name):
            for f in os.listdir(tagsdir):
                if f in ["__init__.py", "__init__.pyc"]:
                    continue
                parts = f.split('.')
                if len(parts) == 2 and parts[1] == "py":
                    add_to_builtins("extensions.%s.templatetags.%s" \
                                        % (ext.name, parts[0]))
        module = __import__(ext.name, globals(), locals(), ['main'])
        module.main.init()
        globals()['extensions'][ext] = module
    
def loadmenus():
    result = []
    for name, mod in extensions.iteritems():
        u = mod.main.urls()
        if u == ():
            continue
        result += (u,)
    return result

def isenabled(ext):
    return extensions.has_key(ext)

def list_extensions():
    basedir = "extensions"
    result = []
    for d in os.listdir(basedir):
        if not os.path.isdir("%s/%s" % (basedir, d)):
            continue
        isvalid = True
        for f in ['urls.py', 'main.py', '__init__.py']:
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
