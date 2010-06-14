import os
from django import template
from mailng.lib import exec_cmd

register = template.Library()

@register.simple_tag
def get_version():
    if os.path.isdir(".hg"):
        version = "dev-"
        code, output = exec_cmd("hg id -i")
        version += output.rstrip()
        return version
    elif os.path.exists("VERSION"):
        code, output = exec_cmd("cat VERSION")
        return output.rstrip()
    else:
        return "Unknown"
