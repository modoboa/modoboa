from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa import userprefs
from modoboa.lib import events
from modoboa.lib.webutils import static_url
from modoboa.admin.lib import is_domain_admin

register = template.Library()

@register.simple_tag
def options_menu(user):
    entries = [
        {"name"  : "userprefs",
         "img"   : static_url("pics/user.png"),
         "label" : _("Options"),
         "class" : "topdropdown",
         "menu"  : [
                {"name" : "changepwd",
                 "url" : reverse(userprefs.views.changepassword),
                 "img" : static_url("pics/edit.png"),
                 "label" : _("Change password"),
                 "class" : "boxed",
                 "rel" : "{handler:'iframe',size:{x:360,y:200},closeBtn:true}"},
                {"name" : "preferences",
                 "img" : static_url("pics/user.png"),
                 "label" : _("Preferences"),
                 "url" : reverse(userprefs.views.preferences),
                 }
                ]
         },
        ]
    if not user.is_superuser and not is_domain_admin(user):
        entries[0]["menu"] += [{
            "name" : "setforwards",
            "url" : reverse(userprefs.views.setforward),
            "img" : static_url("pics/alias.png"),
            "label" : _("Forward"),
            "class" : "boxed",
            "rel" : "{handler:'iframe',size:{x:360,y:350},closeBtn:true}"
            }]

    entries[0]["menu"] += events.raiseQueryEvent("UserMenuDisplay", "options_menu")

    return render_to_string('common/menulist.html', 
                            {"entries" : entries, "user" : user})

@register.simple_tag
def uprefs_menu(user):
    entries = []
    entries += events.raiseQueryEvent("UserMenuDisplay", "uprefs_menu")

    return render_to_string('common/menulist.html', 
                            {"entries" : entries, "user" : user})

@register.simple_tag
def loadextmenu(user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu", user)
    return render_to_string('common/menulist.html', 
                            {"entries" : menu, "user" : user})
