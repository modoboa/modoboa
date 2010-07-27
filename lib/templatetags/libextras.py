# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django import template
from django.contrib import messages
from modoboa.lib import exec_cmd

register = template.Library()

@register.simple_tag
def get_version():
    if os.path.isdir("%s/.hg" % settings.MODOBOA_DIR):
        version = "dev-"
        code, output = exec_cmd("hg id -i", cwd=settings.MODOBOA_DIR)
        version += output.rstrip()
        return version
    elif os.path.exists("%s/VERSION" % settings.MODOBOA_DIR):
        code, output = exec_cmd("cat %s/VERSION" % settings.MODOBOA_DIR)
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


@register.simple_tag
def display_messages(msgs):
    from django.contrib import messages

    text = ""
    level = "info"
    for m in msgs:
        level = m.tags
        text += str(m) + "\\\n"
       
    return """
<script type="text/javascript">
  window.addEvent("domready", function() {
    infobox.%s("%s");
    infobox.hide(2);
  });
</script>
""" % (level, text)

