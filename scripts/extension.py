#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import glob
from django.conf import settings

def usage():
    print "Usage: extension.py <ext name> <on|off>"
    sys.exit(1)

def update_extension(name, extdir, state):
    for d in ['templates', 'scripts']:
        if not os.path.isdir("%s/%s" % (extdir, d)):
	    continue
        cmd = state == "on" \
	    and "ln -s %s/%s %s/%s" % (extdir, d, d, name) \
	    or "rm %s/%s" % (d, name)
	os.system(cmd)

    staticpath = "%s/%s" % (extdir, "static")
    if os.path.isdir(staticpath):
        for d in ['css', 'js']:
            subpath = "%s/%s" % (staticpath, d)
            if not os.path.isdir(subpath):
                continue
            for f in glob.glob("%s/*.%s" % (subpath, d)):
                cmd = state == "on" \
                    and "ln -s %s static/%s" % (f, d) \
                    or "rm static/%s/%s" % (d, os.path.basename(f))
                os.system(cmd)

if __name__ == "__main__":
    if len(sys.argv) != 3:
	usage()
    extdir = "%s/extensions/%s" % (settings.MAILNG_DIR, sys.argv[1])
    if not os.path.isdir(extdir):
	print "Extension not found"
	sys.exit(1)
    extname = "modoboa.extensions.%s" % sys.argv[1]
    update_extension(sys.argv[1], extdir, sys.argv[2])
    if sys.argv[2] == "on":
	print "Make sure you have added '%s' to INSTALLED_APPS (inside settings.py)" % extname
    elif sys.argv[2] == "off":
	print "Make sure you have remove '%s' from INSTALLED_APPS (inside settings.py)" % extname
    
