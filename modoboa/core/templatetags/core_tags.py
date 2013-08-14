import re
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.lib import events


register = template.Library()


@register.simple_tag
def core_menu(selection, user):
    entries = []
    # if user.has_perm("admin.view_domains"):
    #     entries += [
    #         {"name" : "domains",
    #          "url" : reverse("modoboa.admin.views.domains"),
    #          "label" : _("Domains")}
    #         ]
    entries += \
        events.raiseQueryEvent("AdminMenuDisplay", "top_menu", user)
    # if user.has_perm("admin.add_user") or user.has_perm("admin.add_alias"):
    #     entries += [
    #         {"name" : "identities",
    #          "url" : reverse("modoboa.admin.views.identities"),
    #          "label" : _("Identities")},
    #         ]
    if user.is_superuser:
        entries += [
            {"name": "settings",
             "label": _("Modoboa"),
             "url": reverse("modoboa.core.views.admin.viewsettings")}
        ]

    if not len(entries):
        return ""
    return render_to_string("common/menulist.html", {
        "entries": entries,
        "selection": selection,
        "user": user}
    )


@register.simple_tag
def extensions_menu(selection, user):
    menu = events.raiseQueryEvent("UserMenuDisplay", "top_menu", user)
    return render_to_string('common/menulist.html', {
        "selection": selection, "entries": menu, "user": user
    })


@register.simple_tag
def admin_menu(selection, user):
    entries = [
        {"name": "extensions",
         "class": "ajaxlink",
         "url": "extensions/",
         "label": _("Extensions"),
         "img": ""},
        {"name": "info",
         "class": "ajaxlink",
         "url": "info/",
         "label": _("Information")},
        {"name": "logs",
         "class": "ajaxlink",
         "url": "logs/",
         "label": _("Logs")},
        {"name": "parameters",
         "class": "ajaxlink",
         "url": "parameters/",
         "img": "",
         "label": _("Parameters")},
    ]
    return render_to_string('common/menu.html', {
        "entries": entries,
        "css": "nav nav-list",
        "selection": selection,
        "user": user
    })


@register.simple_tag
def user_menu(user, selection):
    entries = [
        {"name": "user",
         "img": "icon-user icon-white",
         "label": user.fullname,
         "menu": [
                {"name": "settings",
                 "img": "icon-list",
                 "label": _("Settings"),
                 "url": reverse("modoboa.core.views.user.index")}
         ]}
    ]

    entries[0]["menu"] += \
        events.raiseQueryEvent("UserMenuDisplay", "options_menu", user) \
        + [{"name": "logout",
            "url": reverse("modoboa.core.views.auth.dologout"),
            "label": _("Logout"),
            "img": "icon-off"}]

    return render_to_string("common/menulist.html", {
        "selection": selection, "entries": entries, "user": user
    })


@register.simple_tag
def uprefs_menu(selection, user):
    entries = [
        {"name": "profile",
         "class": "ajaxlink",
         "url": "profile/",
         "label": _("Profile")},
        {"name": "preferences",
         "class": "ajaxlink",
         "url": "preferences/",
         "label": _("Preferences")},
    ]
    # if user.has_mailbox:
    #     entries.insert(0, {"name": "forward",
    #                        "class": "ajaxlink",
    #                        "url": "forward/",
    #                        "label": _("Forward")})

    entries += events.raiseQueryEvent("UserMenuDisplay", "uprefs_menu", user)
    entries = sorted(entries, key=lambda e: e["label"])
    return render_to_string('common/menu.html', {
        "entries": entries,
        "css": "nav nav-list",
        "selection": selection,
        "user": user
    })


@register.filter
def colorize_level(level):
    classes = {
        "INFO": "text-info",
        "WARNING": "text-warning",
        "CRITICAL": "text-error"
    }
    if not level in classes:
        return level
    return "<p class='%s'>%s</p>" % (classes[level], level)


@register.filter
def tohtml(message):
    return re.sub("'(.*?)'", "<strong>\g<1></strong>", message)
