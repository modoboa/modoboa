from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events
from modoboa.lib.webutils import render_actions
from modoboa.lib.templatetags.lib_tags import render_link

register = template.Library()

genders = {
    "Enabled": (ugettext_lazy("enabled_m"), ugettext_lazy("enabled_f"))
}


@register.simple_tag
def domains_menu(selection, user):
    """Specific menu for domain related operations.

    Corresponds to the menu visible on the left column when you go to
    Domains.

    :param str selection: menu entry currently selected
    :param ``User`` user: connected user
    :rtype: str
    :return: rendered menu (as HTML)
    """
    if not user.has_perm("admin.add_domain"):
        return ""

    entries = [
        {"name": "newdomain",
         "label": _("Add domain"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "admin.newdomain_cb",
         "url": reverse("modoboa.extensions.admin.views.domain.newdomain")},
    ]
    entries += events.raiseQueryEvent("ExtraDomainMenuEntries", user)
    entries += [
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
    """Menu specific to the Identities page.

    :param ``User`` user: the connecter user
    :rtype: str
    :return: the rendered menu
    """
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
         "modalcb": "admin.exportform_cb"
         }
    ]

    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })


@register.simple_tag
def domain_actions(user, domain):
    actions = []
    if domain.__class__.__name__ == 'Domain':
        actions = [
            {"name": "listidentities",
             "url": reverse("modoboa.extensions.admin.views.identity.identities") + "#list/?searchquery=@%s" % domain.name,
             "title": _("View the domain's identities"),
             "img": "icon-user"}
        ]
        if user.has_perm("admin.delete_domain"):
            actions.append({
                "name": "deldomain",
                "url": reverse(
                    "modoboa.extensions.admin.views.domain.deldomain",
                    args=[domain.id]
                ),
                "title": _("Delete %s?" % domain.name),
                "img": "icon-trash"
            })
    else:
        actions = events.raiseQueryEvent('GetDomainActions', user, domain)

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
             "url": reverse("modoboa.extensions.admin.views.alias.delalias") + "?selection=%s" % objid,
             "img": "icon-trash",
             "title": _("Delete %s?" % ident.full_address)},
        ]
    return render_actions(actions)


@register.simple_tag
def domain_modify_link(domain):
    linkdef = {"label": domain.name, "modal": True}
    if domain.__class__.__name__ == "Domain":
        linkdef["url"] = reverse(
            "modoboa.extensions.admin.views.domain.editdomain",
            args=[domain.id]
        )
        linkdef["modalcb"] = "admin.domainform_cb"
    else:
        tmp = events.raiseDictEvent('GetDomainModifyLink', domain)
        for key in ['url', 'modalcb']:
            linkdef[key] = tmp[key]
    return render_link(linkdef)


@register.simple_tag
def domain_aliases(domain):
    """Display domain aliases of this domain.

    :param domain:
    :rtype: str
    """
    if not domain.aliases.count():
        return '---'
    res = ''
    for alias in domain.aliases.all():
        res += '%s<br/>' % alias.name
    return res


@register.simple_tag
def identity_modify_link(identity, active_tab='default'):
    """Return the appropriate modification link.

    According to the identity type, a specific modification link (URL)
    must be used.

    :param identity: a ``User`` or ``Alias`` instance
    :param str active_tab: the tab to display
    :rtype: str
    """
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
