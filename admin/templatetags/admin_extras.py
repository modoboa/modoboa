from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng import admin
from mailng.lib import events

register = template.Library()

genders = {
    "Enabled" : (_("enabled_m"), _("enabled_f"))
}

@register.simple_tag
def domain_menu(domain_id, selection, perms):
    entries = [
        {"name" : "",
         "url" : reverse(admin.views.newmailbox, args=[domain_id]),
         "label" : _("New mailbox"),
         "img" : "/static/pics/add.png",
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:300,y:280}}"},
        {"name" : "mailboxes",
         "url" : reverse(admin.views.mailboxes, args=[domain_id]),
         "img" : "/static/pics/mailbox.png",
         "label" : _("Mailboxes")},
        {"name" : "aliases",
         "url" : reverse("full-aliases", args=[domain_id]),
         "img" : "/static/pics/alias.png",
         "label" : _("Aliases")},
        ]

    if perms.user.has_perm("admin.change_domain"):
        entries += [
            {"name" : "",
             "url" : reverse(admin.views.editdomain, args=[domain_id]),
             "label" : _("Properties"),
             "img" : "/static/pics/edit.png",
             "class" : "boxed",
             "rel" : "{handler:'iframe',size:{x:300,y:180}}"}
            ]
    entries += events.raiseQueryEvent("AdminMenuDisplay", target="admin_menu_bar", 
                                      perms=perms, domain=domain_id)
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries,
                             "perms" : perms})

@register.simple_tag
def settings_menu(selection, perms):
    entries = [
        {"name" : "permissions",
         "url" : reverse(admin.views.settings),
         "label" : _("Permissions"),
         "img" : "/static/pics/permissions.png"},
        {"name" : "addperm",
         "url" : reverse(admin.views.addpermission),
         "img" : "/static/pics/add.png",
         "label" : _("Add permission"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:320,y:210}}"},
        {"name" : "parameters",
         "url" : reverse(admin.views.viewparameters),
         "img" : "/static/pics/domains.png",
         "label" : _("Parameters")},
        ]
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries,
                             "perms" : perms})

@register.simple_tag
def loadadminextmenu(perms):
    menu = events.raiseQueryEvent("AdminMenuDisplay", target="admin_menu_box", 
                                  perms=perms)
    return render_to_string('main/menulist.html', 
                            {"menu" : menu, "perms" : perms})

@register.filter
def gender(value, target):
    if genders.has_key(value):
        return target == "m" and genders[value][0] or genders[value][1]
    return value
