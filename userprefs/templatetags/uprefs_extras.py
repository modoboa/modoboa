from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng import userprefs
from mailng.lib import events

register = template.Library()

@register.simple_tag
def uprefs_menu(perms):
    entries = [
        {"name"  : "userprefs",
         "img"   : "/static/pics/user.png",
         "label" : _("Preferences"),
         "class" : "topdropdown",
         "menu"  : [
                {"name" : "changepwd",
                 "url" : reverse(userprefs.views.changepassword),
                 "img" : "/static/pics/edit.png",
                 "label" : _("Change password"),
                 "class" : "boxed",
                 "rel" : "{handler:'iframe',size:{x:350,y:220}}"}
                ]
         }
        ]
    entries[0]["menu"] += events.raiseQueryEvent("UserMenuDisplay", 
                                                 target="user_menu_bar")

    return render_to_string('common/menulist.html', 
                            {"entries" : entries, "perms" : perms})

@register.simple_tag
def loadextmenu(perms):
    menu = events.raiseQueryEvent("UserMenuDisplay", target="user_menu_box", 
                                  perms=perms)
    return render_to_string('common/menulist.html', 
                            {"entries" : menu, "perms" : perms})
