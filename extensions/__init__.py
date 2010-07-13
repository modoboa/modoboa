# -*- coding: utf-8 -*-
import os
import re
from django.conf import settings

def loadextensions():
    basedir = "%s/extensions" % settings.MAILNG_DIR
    result = []
    for f in os.listdir(basedir):
	if not os.path.isdir("%s/%s" % (basedir, f)):
	    continue
	if not isenabled(f):
	    continue
        module = __import__(f, globals(), locals(), ['main'])
        module.main.init()
   	u = module.main.urls()
        if u == ():
            continue
        result += [u] 
    return result

def isenabled(ext):
    return "modoboa.extensions.%s" % ext in settings.INSTALLED_APPS
