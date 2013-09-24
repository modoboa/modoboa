import re
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events
from modoboa.lib.webutils import static_url, render_actions
from modoboa.lib.templatetags.libextras import render_link

register = template.Library()

genders = {
    "Enabled": (ugettext_lazy("enabled_m"), ugettext_lazy("enabled_f"))
}


@register.simple_tag
def domains_menu(selection, user):
    if not user.has_perm("admin.add_domain"):
        return ""

    entries = [
        {"name": "newdomain",
         "label": _("Add domain"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.newdomain_cb",
         "url": reverse("modoboa.extensions.admin.views.domain.newdomain")},
        {"name": "import",
         "label": _("Import"),
         "img": "icon-folder-open",
         "url": reverse("modoboa.extensions.admin.views.import.import_domains"),
         "modal": True,
         "modalcb": "admin.importform_cb"},
        {"name": "export",
         "label": _("Export"),
         "img": "icon-share-alt",
         "url": reverse("modoboa.extensions.admin.views.export.export_domains"),
         "modal": True,
         "modalcb": "admin.exportform_cb"}
    ]

    return render_to_string('common/menulist.html', {
        "entries": entries,
        "selection": selection,
        "user": user
    })


@register.simple_tag
def identities_menu(user):
    entries = [
        {"name": "identities",
         "label": _("List identities"),
         "img": "icon-user",
         "class": "ajaxlink",
         "url": "list/"},
        {"name": "quotas",
         "label": _("List quotas"),
         "img": "icon-hdd",
         "class": "ajaxlink",
         "url": "quotas/"},
        {"name": "newaccount",
         "label": _("Add account"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.newaccount_cb",
         "url": reverse("modoboa.extensions.admin.views.identity.newaccount")},
        {"name": "newalias",
         "label": _("Add alias"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.aliasform_cb",
         "url": reverse("modoboa.extensions.admin.views.alias.newalias")},
        {"name": "newforward",
         "label": _("Add forward"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.aliasform_cb",
         "url": reverse("modoboa.extensions.admin.views.alias.newforward")},
        {"name": "newdlist",
         "label": _("Add distribution list"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.aliasform_cb",
         "url": reverse("modoboa.extensions.admin.views.alias.newdlist")},
        {"name": "import",
         "label": _("Import"),
         "img": "icon-folder-open",
         "url": reverse("modoboa.extensions.admin.views.import.import_identities"),
         "modal": True,
         "modalcb": "admin.importform_cb"},
        {"name": "export",
         "label": _("Export"),
         "img": "icon-share-alt",
         "url": reverse("modoboa.extensions.admin.views.export.export_identities"),
         "modal": True,
         "modalcb": "admin.exportform_cb"}
    ]

    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })


@register.simple_tag
def domain_actions(user, domid):
    from modoboa.extensions.admin.models import Domain

    domain = Domain.objects.get(pk=domid)
    actions = [
        {"name": "listidentities",
         "url": reverse("modoboa.extensions.admin.views.identity.identities") + "#list/?searchquery=@%s" % domain.name,
         "title": _("View the domain's identities"),
         "img": "icon-user"}
    ]
    if user.has_perm("admin.delete_domain"):
        actions.append({
            "name": "deldomain",
            "url": reverse("modoboa.extensions.admin.views.domain.deldomain", args=[domid]),
            "title": _("Delete %s?" % domain.name),
            "img": "icon-trash"
        })
    return render_actions(actions)


@register.simple_tag
def identity_actions(user, ident):
    name = ident.__class__.__name__
    objid = ident.id
    if name == "User":
        actions = events.raiseQueryEvent("ExtraAccountActions", ident)
        actions += [
            {"name": "delaccount",
             "url": reverse("modoboa.extensions.admin.views.identity.delaccount", args=[objid]),
             "img": "icon-trash",
             "title": _("Delete %s?" % ident.username)},
        ]
    else:
        actions = [
            {"name": "delalias",
             "url": reverse("modoboa.admin.views.delalias") + "?selection=%s" % objid,
             "img": "icon-trash",
             "title": _("Delete %s?" % ident.full_address)},
        ]
    return render_actions(actions)


@register.simple_tag
def identity_modify_link(identity, active_tab='default'):
    linkdef = {"label": identity.identity, "modal": True}
    if identity.__class__.__name__ == "User":
        linkdef["url"] = reverse(
            "modoboa.extensions.admin.views.identity.editaccount",
            args=[identity.id]
        )
        linkdef["url"] += "?active_tab=%s" % active_tab
        linkdef["modalcb"] = "admin.editaccount_cb"
    else:
        linkdef["url"] = reverse(
            "modoboa.extensions.admin.views.alias.editalias",
            args=[identity.id]
        )
        linkdef["modalcb"] = "admin.aliasform_cb"
    return render_link(linkdef)


@register.simple_tag
def domadmin_actions(daid, domid):
    actions = [{
        "name": "removeperm",
        "url": reverse("modoboa.extensions.admin.views.identity.remove_permission") + "?domid=%s&daid=%s" % (domid, daid),
        "img": "icon-trash",
        "title": _("Remove this permission")
    }]
    return render_actions(actions)


@register.simple_tag
def loadadminextmenu(user):
    menu = events.raiseQueryEvent("AdminMenuDisplay", "admin_menu_box", user)
    return render_to_string('common/menulist.html',
                            {"entries": menu, "user": user})


@register.simple_tag
def param(app, definition):
    name = "%s.%s" % (app, definition["name"])
    value = definition["value"] \
        if "value" in definition else definition["deflt"]

    if definition["type"] == "separator":
        return "<h5>%s</h5>" % (unicode(definition["label"]))

    extratags = ""
    if "visible_if" in definition:
        vfield, vvalue = definition["visible_if"].split("=")
        extratags = "data-visibility-field='%s.%s' data-visibility-value='%s'" \
            % (app, vfield, vvalue)

    result = """<div class='control-group'%s>
  <label class="param-label" for="%s">%s</label>
""" % (extratags, name,
       _(definition["label"]) if "label" in definition else definition["name"])

    result += "<div class='param-controls'>"
    if definition["type"] in ["string", "int"]:
        result += """
  <input type='text' name='%s' id='%s' value='%s' />""" % (name, name, value)

    if definition["type"] == "text":
        result += "<textarea name='%s' id='%s'>%s</textarea>" \
            % (name, name, value)

    if definition["type"] == "list_yesno":
        for idx, v in enumerate([("yes", _("Yes")), ("no", _("No"))]):
            checked = "checked" if value == v[0] else ""
            result += """<label for="%(id)s" class="radio inline">
  <input type="radio" name="%(name)s" id="%(id)s" value="%(value)s"%(checked)s />
  %(label)s
</label>
""" % dict(id="%s_%d" % (name, idx), name=name, value=v[0],
           label=v[1], checked=checked)

    if definition["type"] == "list":
        result += """
<select name='%s' id='%s'>""" % (name, name)
        values = []
        if "values" in definition:
            values = definition["values"]
        for v in values:
            selected = ""
            if value == v[0]:
                selected = " selected='selected'"
            result += "<option value='%s'%s>%s</option>\n" % (v[0], selected, v[1].decode("utf-8"))
        result += """
</select>
"""

    if "help" in definition:
        result += """<a class="help" rel="popover" data-content="%s" data-original-title="%s">
  <i class="icon-info-sign"></i>
</a>""" % (unicode(definition["help"]), _("Help"))
#         result += """
# <span class="help-block">%s</span>
# """ % _(definition["help"])

    result += """
  </div>
</div>
"""
    return result


@register.filter
def gender(value, target):
    if value in genders:
        trans = target == "m" and genders[value][0] or genders[value][1]
        if trans.find("_") == -1:
            return trans
    return value


@register.simple_tag
def get_extra_admin_content(user, target, currentpage):
    res = events.raiseQueryEvent(
        "ExtraAdminContent", user, target, currentpage
    )
    return "".join(res)
