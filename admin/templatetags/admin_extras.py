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
def admin_menu(selection, user):
    entries = []
    if user.has_perm("admin.view_domains"):
        entries += [
            {"name" : "domains",
             "url" : reverse(admin.views.domains),
             "label" : _("Domains")}
            ]
    entries += \
        events.raiseQueryEvent("AdminMenuDisplay", "top_menu", user)
    if user.has_perm("auth.add_user") or user.has_perm("admin.add_alias"):
        entries += [
            {"name" : "identities",
             "url" : reverse(admin.views.identities),
             "label" : _("Identities")},
            ]
    if user.is_superuser:
        entries += [
            {"name" : "settings",
             "label" : _("Modoboa"),
             "url" : reverse(admin.views.viewparameters)}
            ]

    if not len(entries):
        return ""
    return render_to_string("common/menulist.html",
                            {"entries" : entries, "selection" : selection, "user" : user})
        
@register.simple_tag
def settings_menu(selection, user):
    entries = [
        {"name" : "extensions",
         "url" : reverse(admin.views.viewextensions),
         "label" : _("Extensions"),
         "img" : static_url("pics/extensions.png")},
        {"name" : "parameters",
         "url" : reverse(admin.views.viewparameters),
         "img" : static_url("pics/domains.png"),
         "label" : _("Parameters")},
        ]
    return render_to_string('common/menu.html', {
            "entries" : entries, 
            "css" : "nav nav-list",
            "selection" : selection,
            "user" : user
            })

@register.simple_tag
def domains_menu(selection, user):
    entries = [
        {"name" : "newdomain",
         "label" : _("New domain"),
         "img" : "icon-plus",
         "modal" : True,
         "modalcb" : "domainform_cb",
         "url" : reverse("modoboa.admin.views.newdomain")},
        {"name" : "import",
         "label" : _("Import"),
         "img" : "icon-folder-open",
         "url" : reverse(admin.views.import_domains),
         "modal" : True,
         "modalcb" : "importform_cb"}
        ]
    return render_to_string('common/menu.html', {
            "entries" : entries, 
            "css" : "nav nav-list",
            "selection" : selection,
            "user" : user
            })        

@register.simple_tag
def identities_menu(user):
    entries = [
        {"name" : "newaccount",
         "label" : _("New account"),
         "img" : "icon-plus",
         "modal" : True,
         "modalcb" : "newaccount_cb",
         "url" : reverse(admin.views.newaccount)},
        {"name" : "newdlist",
         "label" : _("New distribution list"),
         "img" : "icon-plus",
         "modal" : True,
         "modalcb" : "dlistform_cb",
         "url" : reverse(admin.views.newdlist)},
        {"name" : "import",
         "label" : _("Import"),
         "img" : "icon-folder-open",
         "url" : reverse(admin.views.import_identities),
         "modal" : True,
         "modalcb" : "importform_cb"}
        ]

    return render_to_string('common/menu.html', {
            "entries" : entries, 
            "css" : "nav nav-list",
            "user" : user
            })

@register.simple_tag
def domain_actions(user, domid):
    actions = [
        {"name" : "deldomain",
         "url" : reverse(admin.views.deldomain) + "?selection=%s" % domid,
         "img" : "icon-trash"},         
        ]

    return render_actions(actions)

@register.simple_tag
def identity_actions(user, iid):
    name, objid = iid.split(':')
    if name == "User":
        actions = [
            {"name" : "delaccount",
             "url" : reverse(admin.views.delaccount) + "?selection=%s" % objid,
             "img" : "icon-trash",
             "title" : _("Delete this account")},
            ]
    else:
        actions = [
            {"name" : "deldlist",
             "url" : reverse(admin.views.deldlist) + "?selection=%s" % objid,
             "img" : "icon-trash",
             "title" : _("Delete this distribution list")},
            ]
    return render_actions(actions)

@register.simple_tag
def domadmin_actions(daid, domid):
    actions = [dict(
            name="removeperm",
            url=reverse(admin.views.remove_permission) + "?domid=%s&daid=%s" % (domid, daid),
            img="icon-trash",
            title=_("Remove this permission")
            )]
    return render_actions(actions)

@register.simple_tag
def loadadminextmenu(user):
    menu = events.raiseQueryEvent("AdminMenuDisplay", "admin_menu_box", user)
    return render_to_string('common/menulist.html', 
                            {"entries" : menu, "user" : user})

@register.simple_tag
def param(app, definition):
    name = "%s.%s" % (app, definition["name"])
    value = definition.has_key("value") \
        and definition["value"] or definition["deflt"]

    result = """<div class='control-group'>
  <label class="param-label" for="%s">%s</label>
  <div class="param-controls">""" \
        % (name, definition.has_key("label") and _(definition["label"]) 
           or definition["name"])
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
            result += "<option value='%s'%s>%s</option>\n" % (v[0], selected, v[1].decode("utf-8"))
        result += """
</select>
"""

    if definition.has_key("help"):
        result += """
<p class="help-block">%s</p>
""" % definition["help"]
    result += """
  </div>
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
def get_extra_admin_content(user, target, currentpage):
    res = events.raiseQueryEvent("ExtraAdminContent", user, target, currentpage)
    return "".join(res)
