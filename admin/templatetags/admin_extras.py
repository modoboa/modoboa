from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _, ugettext_noop
from django.core.urlresolvers import reverse
from modoboa import admin
from modoboa.lib import events
from modoboa.lib.webutils import static_url, render_actions

register = template.Library()

genders = {
    "Enabled" : (ugettext_noop("enabled_m"), ugettext_noop("enabled_f"))
}

@register.simple_tag
def admin_menu(user):
    entries = [
        {"name" : "admin",
         "img" : static_url('pics/admin.png'),
         "label" : _("Admin"),
         "class" : "topdropdown",
         "menu" : []
         }
        ]
    if user.has_perm("admin.view_domains"):
        entries[0]["menu"] += [
            {"name" : "domains",
             "url" : reverse(admin.views.domains),
             "label" : _("Domains"),
             "img" : static_url("pics/domains.png")}
            ]
    elif user.has_perm("admin.view_mailboxes"):
        entries[0]["menu"] += [
            {"name" : "mailboxes",
             "url" : reverse(admin.views.domains),
             "label" : _("Mailboxes"),
             "img" : static_url("pics/mailbox.png")}
            ]
    entries[0]["menu"] += \
        events.raiseQueryEvent("AdminMenuDisplay", "top_menu", user)
    if user.has_perm("auth.view_permissions"):
        entries[0]["menu"] += [
            {"name" : "permissions",
             "url" : reverse(admin.views.permissions),
             "label" : _("Permissions"),
             "img" : static_url("pics/permissions.png")}
            ]
    if user.is_superuser:
        entries[0]["menu"] += [
            {"name" : "settings",
             "img" : static_url("pics/settings.png"),
             "label" : _("Settings"),
             "url" : reverse(admin.views.viewparameters)}
            ]

    if not len(entries[0]["menu"]):
        return ""
    return render_to_string("common/menulist.html",
                            {"entries" : entries, "user" : user})
        
@register.simple_tag
def settings_menu(selection, user):
    entries = [
        {"name" : "parameters",
         "url" : reverse(admin.views.viewparameters),
         "img" : static_url("pics/domains.png"),
         "label" : _("Parameters")},
        {"name" : "extensions",
         "url" : reverse(admin.views.viewextensions),
         "label" : _("Extensions"),
         "img" : static_url("pics/extensions.png")},
        ]
    return render_to_string('common/menu.html', 
                            {"selection" : selection, "entries" : entries,
                             "user" : user})

def dommenu_entry(name, label, img, listurl, newurl):
    result = {"name" : name,
              "label" : label,
              "img" : img,
              "url" : listurl,
              "class" : "menubardropdown",
              }
    return result

@register.simple_tag
def domains_menu(selection, user, domid):
    args = domid != "" and ("?domid=%s" % domid) or ""
    entries = []
    if selection == "stats":
        disabled = True
    else:
        disabled = False
    
    entries += [
        {"name" : "actions",
         "label" : _("Actions"),
         "img" : static_url("pics/tools.png"),
         "class" : "menubardropdown",
         "menu" : [
                {"name" : "new",
                 "label" : _("New"),
                 "img" : static_url("pics/add.png"),
                 "disabled" : disabled},
                {"name" : "remove",
                 "label" : _("Remove"),
                 "img" : static_url("pics/remove.png"),
                 "disabled" : disabled
                 },
                {"name" : "import",
                 "label" : _("Import data"),
                 "img" : static_url("pics/import.png"),
                 "class" : "boxed",
                 "rel" : "{handler:'iframe',size:{x:370,y:250}}",
                 "url" : reverse(admin.views.importdata)}
                ]
         },
        ]

    entries += [{"separator" : True}]
    if user.has_perm("admin.view_domains"):
        entries += dommenu_entry("domains", _("Domains"), 
                                 static_url("pics/domains.png"),
                                 reverse(admin.views.domains), 
                                 reverse(admin.views.newdomain)),
    entries += [
        dommenu_entry("domaliases", _("Domain aliases"), static_url("pics/alias.png"),
                      reverse(admin.views.domaliases) + args, 
                      reverse(admin.views.newdomalias) + args),
        dommenu_entry("mailboxes", _("Mailboxes"), static_url("pics/mailbox.png"),
                      reverse(admin.views.mailboxes) + args, 
                      reverse(admin.views.newmailbox) + args),
        dommenu_entry("mbaliases", _("Mailbox aliases"), static_url("pics/alias.png"),
                      reverse(admin.views.mbaliases) + args, 
                      reverse(admin.views.newmbalias) + args),
        ]
    entries += events.raiseQueryEvent("AdminMenuDisplay", "admin_menu_box", user)
    return render_to_string('common/menu.html', 
                            {"entries" : entries, 
                             "selection" : selection,
                             "user" : user})

@register.simple_tag
def permissions_menu(user):
    entries = [
        {"name" : "addperm",
         "label" : _("Add permission"),
         "img" : static_url("pics/add.png"),
         "url" : reverse(admin.views.add_permission)},
        {"name" : "delperms",
         "label" : _("Remove permissions"),
         "img" : static_url("pics/remove.png"),
         "url" : reverse(admin.views.delete_permissions)},
        ]
    return render_to_string('common/menu.html', 
                            {"entries" : entries, "user" : user})

@register.simple_tag
def domain_actions(user, domid):
    actions = [
        {"name" : "editdomain",
         "url" : reverse(admin.views.editdomain, args=[domid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit domain"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:310,y:190}}"},
        {"name" : "domaliases",
         "url" : reverse(admin.views.domaliases) + "?domid=%s" % domid,
         "img" : static_url("pics/alias.png"),
         "title" : _("View aliases of this domain")}
        ]
    if user.has_perm('admin.view_domains'):
        actions += [
            {"name" : "viewadmins",
             "url" : reverse(admin.views.view_domain_admins, args=[domid]),
             "img" : static_url("pics/administrators.png"),
             "title" : _("View administrators of this domain"),
             "class" : "boxed",
             "rel" : "{handler:'iframe',size:{x:310,y:190}}"},
            ]
    return render_actions(actions)

@register.simple_tag
def domalias_actions(user, aid):
    actions = [
        {"name" : "editalias",
         "url" : reverse(admin.views.editdomalias, args=[aid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit alias"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:310,y:190}}"}
        ]
    return render_actions(actions)

@register.simple_tag
def mailbox_actions(user, mboxid):
    actions = [
        {"name" : "editmailbox",
         "url" : reverse(admin.views.editmailbox, args=[mboxid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit mailbox"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:310,y:320}}"},
        {"name" : "aliases",
         "url" : reverse(admin.views.mbaliases) + "?mbid=%d" % mboxid,
         "img" : static_url("pics/alias.png"),
         "title" : _("View this mailbox aliases")},
        ]
    return render_actions(actions)

@register.simple_tag
def domain_admin_actions(user, daid):
    from modoboa.admin.models import User

    actions = [
        {"name" : "editdomainadmin",
         "url" : reverse(admin.views.edit_domain_admin, args=[daid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit domain admin"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:350,y:320}}"},
        {"name" : "assigndomains",
         "url" : reverse(admin.views.assign_domains_to_admin, args=[daid]),
         "img" : static_url("pics/domains.png"),
         "title" : _("Assign domain(s) to this administrator"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:350,y:320}}"},
        ]
    actions += events.raiseQueryEvent("DomainAdminActions", User.objects.get(pk=daid))
    return render_actions(actions)

@register.simple_tag
def mbalias_actions(user, aliasid):
    from modoboa.admin.models import Alias

    alias = Alias.objects.get(pk=aliasid)
    if alias.ui_disabled(user):
        return "--"
    actions = [
        {"name" : "editmbalias",
         "url" : reverse(admin.views.editmbalias, args=[aliasid]),
         "img" : static_url("pics/edit.png"),
         "title" : _("Edit mailbox alias"),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:320,y:300}}"}
        ]
    return render_actions(actions)

@register.simple_tag
def loadadminextmenu(user):
    menu = events.raiseQueryEvent("AdminMenuDisplay", "admin_menu_box", user)
    return render_to_string('common/menulist.html', 
                            {"entries" : menu, "user" : user})

@register.simple_tag
def param(app, definition):
    result = """<div class='row'>
  <label>%s</label>""" % (definition.has_key("label") \
                              and _(definition["label"]) or definition["name"])
    name = "%s.%s" % (app, definition["name"])
    value = definition.has_key("value") \
        and definition["value"] or definition["deflt"]

    if definition["type"] in ["string", "int"]:
        result += """
  <input type='text' name='%s' id='%s' value='%s' />""" % (name, name, value)

    if definition["type"] == "text":
        result += "<textarea name='%s' id='%s'>%s</textarea>" \
            % (name, name, value)

    if definition["type"] in ["list", "list_yesno"]:
        result += """
<select name='%s' id='%s'>""" % (name, name)
        values = []
        if definition["type"] == "list_yesno":
            values = [("yes", _("Yes")), ("no", _("No"))]
        else:
            if definition.has_key("values"):
                values = definition["values"]
        for v in values:
            selected = ""
            if value == v[0]:
                selected = " selected='selected'"
            result += "<option value='%s'%s>%s</option>\n" % (v[0], selected, v[1])
        result += """
</select>
"""

    if definition.has_key("help"):
        result += """
  <a href='%s' onclick='return false;' class='Tips' title='%s'>
    <img src='%s' border='0' />
  </a>""" % (_(definition["help"]), _("Help"), static_url("pics/info.png"))
    result += """
</div>
"""
    return result

@register.filter
def gender(value, target):
    if genders.has_key(value):
        trans = target == "m" and genders[value][0] or genders[value][1]
        if trans.find("_") == -1:
            return trans
    return value

@register.simple_tag
def get_footer_content(user, objtype):
    res = events.raiseQueryEvent("AdminFooterDisplay", user, objtype)
    return "".join(res)
