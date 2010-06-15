import os
from django.conf import settings
from django import template
from mailng.lib import exec_cmd

register = template.Library()

@register.simple_tag
def get_version():
    if os.path.isdir("%s/.hg" % settings.MAILNG_DIR):
        version = "dev-"
        code, output = exec_cmd("hg id -i", cwd=settings.MAILNG_DIR)
        version += output.rstrip()
        return version
    elif os.path.exists("%s/VERSION" % settings.MAILNG_DIR):
        code, output = exec_cmd("cat %s/VERSION" % settings.MAILNG_DIR)
        return output.rstrip()
    else:
        return "Unknown"

@register.simple_tag
def join(items, sep=','):
    res = ""
    for k, v in items.iteritems():
        if res != "":
            res += sep
        res += "%s : '%s'" % (k, v)
    return res
