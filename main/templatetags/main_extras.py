from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng import main
from mailng.lib import events

register = template.Library()

@register.simple_tag
def menu(selection, perms):
    entries = [
        {"name" : "autoreply",
         "url" : reverse(main.views.autoreply),
         "img" : "/static/pics/auto-reply.png",
         "label" : _("Auto-reply message")},
        {"name" : "changepwd",
         "url" : reverse(main.views.changepassword),
         "img" : "/static/pics/edit.png",
         "label" : _("Change password"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:350,y:220}}"}
        ]

    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})

@register.simple_tag
def loadextmenu(perms):
    menu = events.raiseQueryEvent("UserMenuDisplay")
    return render_to_string('main/menulist.html', 
                            {"menu" : menu, "perms" : perms})
