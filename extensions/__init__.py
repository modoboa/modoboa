# -*- coding: utf-8 -*-
import os
import re

extensions = []

def loadextensions():
    from django.conf import settings

    expr = re.compile("mailng\.extensions\.(.+)")
    for app in settings.INSTALLED_APPS:
        m = expr.match(app)
        if not m:
            continue
        module = __import__(m.group(1), globals(), locals(), ['main'])
        module.main.init()
        globals()['extensions'] += [module]
    
def loadmenus():
    result = []
    for mod in extensions:
        u = mod.main.urls()
        if u == ():
            continue
        result += (u,)
    return result

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
                result += [module.main.infos()]
            except AttributeError:
                pass
    return result
