"""Admin extension tags."""

from django import template
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib import events
from modoboa.lib.templatetags.lib_tags import render_link
from modoboa.lib.web_utils import render_actions

from .. import signals

register = template.Library()

genders = {
    "Enabled": (ugettext_lazy("enabled_m"), ugettext_lazy("enabled_f"))
}


@register.simple_tag
def domains_menu(selection, user, ajax_mode=True):
    """Specific menu for domain related operations.

    Corresponds to the menu visible on the left column when you go to
    *Domains*.

    :param str selection: menu entry currently selected
    :param ``User`` user: connected user
    :rtype: str
    :return: rendered menu (as HTML)
    """
    domain_list_url = (
        "list/" if ajax_mode else reverse("admin:domain_list")
    )
    entries = [
        {"name": "domains",
         "label": _("List domains"),
         "img": "fa fa-user",
         "class": "ajaxnav navigation",
         "url": domain_list_url},
        {"name": "statistics",
         "label": _("Statistics"),
         "img": "fa fa-line-chart",
         "class": "navigation",
         "url": reverse("admin:domain_statistics")}
    ]
    if user.has_perm("admin.add_domain"):
        entries += events.raiseQueryEvent("ExtraDomainMenuEntries", user)
        entries += [
            {"name": "import",
             "label": _("Import"),
             "img": "fa fa-folder-open",
             "url": reverse("admin:domain_import"),
             "modal": True,
             "modalcb": "admin.importform_cb"},
            {"name": "export",
             "label": _("Export"),
             "img": "fa fa-share-alt",
             "url": reverse("admin:domain_export"),
             "modal": True,
             "modalcb": "admin.exportform_cb"}
        ]

    return render_to_string('common/menulist.html', {
        "entries": entries,
        "selection": selection,
        "user": user
    })


@register.simple_tag
def identities_menu(user, selection=None, ajax_mode=True):
    """Menu specific to the Identities page.

    :param ``User`` user: the connecter user
    :rtype: str
    :return: the rendered menu
    """
    nav_classes = "navigation"
    if ajax_mode:
        identity_list_url = "list/"
        quota_list_url = "quotas/"
        nav_classes += " ajaxnav"
    else:
        identity_list_url = reverse("admin:identity_list")
        quota_list_url = identity_list_url + "#quotas/"
    entries = [
        {"name": "identities",
         "label": _("List identities"),
         "img": "fa fa-user",
         "class": nav_classes,
         "url": identity_list_url},
        {"name": "quotas",
         "label": _("List quotas"),
         "img": "fa fa-hdd-o",
         "class": nav_classes,
         "url": quota_list_url},
        {"name": "import",
         "label": _("Import"),
         "img": "fa fa-folder-open",
         "url": reverse("admin:identity_import"),
         "modal": True,
         "modalcb": "admin.importform_cb"},
        {"name": "export",
         "label": _("Export"),
         "img": "fa fa-share-alt",
         "url": reverse("admin:identity_export"),
         "modal": True,
         "modalcb": "admin.exportform_cb"}
    ]

    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })


@register.simple_tag
def domain_actions(user, domain):
    actions = [
        {"name": "listidentities",
         "url": u"{0}#list/?searchquery=@{1}".format(
             reverse("admin:identity_list"), domain.name),
         "title": _("View the domain's identities"),
         "img": "fa fa-user"}
    ]
    if user.has_perm("admin.change_domain"):
        actions.append({
            "name": "editdomain",
            "title": _("Edit {}").format(domain),
            "url": reverse("admin:domain_change", args=[domain.pk]),
            "modal": True,
            "modalcb": "admin.domainform_cb",
            "img": "fa fa-edit"
        })
    if user.has_perm("admin.delete_domain"):
        actions.append({
            "name": "deldomain",
            "url": reverse("admin:domain_delete", args=[domain.id]),
            "title": _("Delete %s?" % domain.name),
            "img": "fa fa-trash"
        })

    responses = signals.extra_domain_actions.send(
        sender=None, user=user, domain=domain)
    for receiver, response in responses:
        if response:
            actions += response

    return render_actions(actions)


@register.simple_tag
def identity_actions(user, ident):
    name = ident.__class__.__name__
    objid = ident.id
    if name == "User":
        actions = events.raiseQueryEvent("ExtraAccountActions", ident)
        url = (
            reverse("admin:account_change", args=[objid]) +
            "?active_tab=default"
        )
        actions += [
            {"name": "changeaccount",
             "url": url,
             "img": "fa fa-edit",
             "modal": True,
             "modalcb": "admin.editaccount_cb",
             "title": _("Edit {}").format(ident.username)},
            {"name": "delaccount",
             "url": reverse("admin:account_delete", args=[objid]),
             "img": "fa fa-trash",
             "title": _("Delete %s?" % ident.username)},
        ]
    else:
        actions = [
            {"name": "changealias",
             "url": reverse("admin:alias_change", args=[objid]),
             "img": "fa fa-edit",
             "modal": True,
             "modalcb": "admin.aliasform_cb",
             "title": _("Edit {}").format(ident)},
            {"name": "delalias",
             "url": "{}?selection={}".format(
                 reverse("admin:alias_delete"), objid),
             "img": "fa fa-trash",
             "title": _("Delete %s?" % ident.address)},
        ]
    return render_actions(actions)


@register.simple_tag
def check_identity_status(identity):
    """Check if identity is enabled or not."""
    if identity.__class__.__name__ == "User":
        if hasattr(identity, "mailbox") \
           and not identity.mailbox.domain.enabled:
            return False
        elif not identity.is_active:
            return False
    elif not identity.enabled or not identity.domain.enabled:
        return False
    return True


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
    return mark_safe(res)


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
        linkdef["url"] = reverse("admin:account_change", args=[identity.id])
        linkdef["url"] += "?active_tab=%s" % active_tab
        linkdef["modalcb"] = "admin.editaccount_cb"
    else:
        linkdef["url"] = reverse("admin:alias_change", args=[identity.id])
        linkdef["modalcb"] = "admin.aliasform_cb"
    return render_link(linkdef)


@register.simple_tag
def domadmin_actions(daid, domid):
    actions = [{
        "name": "removeperm",
        "url": "{0}?domid={1}&daid={2}".format(
            reverse("admin:permission_remove"), domid, daid),
        "img": "fa fa-trash",
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
    return mark_safe("".join(res))
