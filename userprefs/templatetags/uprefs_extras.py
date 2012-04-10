from django import template
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa import userprefs
from modoboa.lib import events
from modoboa.lib.webutils import static_url

register = template.Library()

@register.simple_tag
def uprefs_menu(selection, user):
    entries = [
        {"name" : "preferences",
         "url" : "",
         "label" : _("Preferences")},
        ]
    entries += events.raiseQueryEvent("UserMenuDisplay", "uprefs_menu", user)

    return render_to_string('common/menu.html', {
            "entries" : entries, 
            "css" : "nav nav-list",
            "selection" : selection,
            "user" : user
            })


@register.simple_tag
def user_menu(user, selection):
    entries = [
        {"name" : "user",
         "img" : "icon-user icon-white",
         "label" : user.fullname,
         "menu" : [
                {"name" : "changepwd",
                 "url" : reverse("modoboa.userprefs.views.changepassword"),
                 "img" : "icon-edit",
                 "label" : _("Change password"),
                 "modal" : True,
                 "modalcb" : "chpasswordform_cb"},
                {"name" : "settings",
                 "img" : "icon-list",
                 "label" : _("Settings"),
                 "url" : reverse("modoboa.userprefs.views.preferences")}
                ]}
        ]
    entries[0]["menu"] += \
        events.raiseQueryEvent("UserMenuDisplay", "options_menu", user) \
        + [{"name" : "logout",
            "url" : reverse("modoboa.auth.views.dologout"),
            "label" : _("Logout"),
            "img" : "icon-off"}]

    # if user.group == 'SimpleUsers':
    #     entries[0]["menu"] += [{
    #         "name" : "setforwards",
    #         "url" : reverse("modoboa.userprefs.views.setforward"),
    #         "img" : static_url("pics/alias.png"),
    #         "label" : _("Forward"),
    #         "class" : "boxed",
    #         "rel" : "{handler:'iframe',size:{x:360,y:350},closeBtn:true}"
    #         }]

    return render_to_string("common/menulist.html",
                            {"selection" : selection, "entries" : entries, "user" : user})

@register.simple_tag
def loadextmenu(selection, user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu", user)
    return render_to_string('common/menulist.html', 
                            {"selection" : selection, "entries" : menu, "user" : user})
