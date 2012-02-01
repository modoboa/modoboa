# coding: utf-8

from django import template
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from modoboa.lib.webutils import static_url, render_actions
from modoboa.extensions.limits import views

register = template.Library()

@register.simple_tag
def resellers_menu(user):
    entries = [{"name" : "new",
                "label" : _("New"),
                "img" : static_url("pics/add.png"),
                "class" : "boxed",
                "rel" : "{handler:'iframe',size:{x:350,y:300}}",
                "url" : reverse(views.new_reseller)},
               {"name" : "remove",
                "label" : _("Remove"),
                "img" : static_url("pics/remove.png"),
                "url" : reverse(views.delete_resellers)
                }]
    return render_to_string("common/menulist.html",
                            {"entries" : entries, "user" : user})

@register.simple_tag
def reseller_actions(user, resid):
    actions = [
        {"name" : "editreseller",
         "url" : reverse(views.edit_reseller, args=[resid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit reseller"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:350,y:300}}"},
        {"name" : "editlimits",
         "url" : reverse(views.edit_limits_pool, args=[resid]),
         "img" : static_url("pics/settings.png"),
         "title" : _("Edit limits allocated to this reseller"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:330,y:310}}"},
        ]
    return render_actions(actions)
