# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django import template
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events
from modoboa.lib.sysutils import exec_cmd
from modoboa.lib.webutils import static_url

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
        text += unicode(m) + "\\\n"
       
    return """
<script type="text/javascript">
  window.addEvent("domready", function() {
    infobox.%s("%s");
    infobox.hide(2);
  });
</script>
""" % (level, text)

@register.simple_tag
def load_optionalmenu(user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu_middle", user)
    return template.loader.render_to_string('common/menulist.html', 
                                            {"entries" : menu, "user" : user})

@register.simple_tag
def user_menu(user):
    entries = [
        {"name" : "user",
         "img" : static_url('pics/administrators.png'),
         "label" : user.fullname,
         "class" : "topdropdown",
         "menu" : [
                {"name" : "changepwd",
                 "url" : reverse("modoboa.userprefs.views.changepassword"),
                 "img" : static_url("pics/edit.png"),
                 "label" : _("Change password"),
                 "class" : "boxed",
                 "rel" : "{handler:'iframe',size:{x:360,y:200},closeBtn:true}"},
                {"name" : "preferences",
                 "img" : static_url("pics/user.png"),
                 "label" : _("Preferences"),
                 "url" : reverse("modoboa.userprefs.views.preferences")},
                {"name" : "logout",
                 "url" : reverse("modoboa.auth.views.dologout"),
                 "label" : _("Logout"),
                 "img" : static_url("pics/logout.png")}
                ]
         }
        ]
    if user.belongs_to_group('SimpleUsers'):
        entries[0]["menu"] += [{
            "name" : "setforwards",
            "url" : reverse("modoboa.userprefs.views.setforward"),
            "img" : static_url("pics/alias.png"),
            "label" : _("Forward"),
            "class" : "boxed",
            "rel" : "{handler:'iframe',size:{x:360,y:350},closeBtn:true}"
            }]

    entries[0]["menu"] += events.raiseQueryEvent("UserMenuDisplay", "options_menu", user)

    return render_to_string("common/menulist.html",
                            {"entries" : entries, "user" : user})
