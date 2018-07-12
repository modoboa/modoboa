# -*- coding: utf-8 -*-

"""Custom tags for Core application."""

from __future__ import unicode_literals

import os
import re
from functools import reduce

import pkg_resources

from django import template
from django.conf import settings
from django.contrib.sessions.models import Session
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, ugettext as _

from .. import models
from .. import signals

register = template.Library()


@register.simple_tag
def core_menu(selection, user):
    """Build the top level menu."""
    entries = signals.extra_admin_menu_entries.send(
        sender="core_menu", location="top_menu", user=user)
    entries = reduce(lambda a, b: a + b, [entry[1] for entry in entries])
    if user.is_superuser:
        entries += [
            {"name": "settings",
             "label": _("Modoboa"),
             "url": reverse("core:index")}
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
    menu = signals.extra_user_menu_entries.send(
        sender="core_menu", location="top_menu", user=user)
    menu = reduce(lambda a, b: a + b, [entry[1] for entry in menu])
    return render_to_string("common/menulist.html", {
        "selection": selection, "entries": menu, "user": user
    })


@register.simple_tag
def admin_menu(selection, user):
    entries = [
        {"name": "info",
         "class": "ajaxnav",
         "url": "info/",
         "label": _("Information")},
        {"name": "logs",
         "class": "ajaxnav",
         "url": "logs/?sort_order=-date_created",
         "label": _("Logs")},
        {"name": "parameters",
         "class": "ajaxnav",
         "url": "parameters/",
         "img": "",
         "label": _("Parameters")},
    ]
    return render_to_string("common/menu.html", {
        "entries": entries,
        "css": "nav nav-sidebar",
        "selection": selection,
        "user": user
    })


@register.simple_tag
def user_menu(user, selection):
    entries = [
        {"name": "user",
         "img": "fa fa-user",
         "label": user.fullname,
         "menu": [
                {"name": "settings",
                 "img": "fa fa-list",
                 "label": _("Settings"),
                 "url": reverse("core:user_index")}
         ]}
    ]

    extra_entries = signals.extra_user_menu_entries.send(
        sender="user_menu", location="options_menu", user=user)
    extra_entries = reduce(
        lambda a, b: a + b, [entry[1] for entry in extra_entries])
    entries[0]["menu"] += (
        extra_entries + [{"name": "logout",
                          "url": reverse("core:logout"),
                          "label": _("Logout"),
                          "img": "fa fa-sign-out"}]
    )
    return render_to_string("common/menulist.html", {
        "selection": selection, "entries": entries, "user": user
    })


@register.simple_tag
def uprefs_menu(selection, user):
    entries = [
        {"name": "profile",
         "class": "ajaxnav",
         "url": "profile/",
         "label": _("Profile")},
        {"name": "preferences",
         "class": "ajaxnav",
         "url": "preferences/",
         "label": _("Preferences")},
    ]
    if user.is_superuser:
        entries.append({
            "name": "api",
            "class": "ajaxnav",
            "url": "api/",
            "label": _("API"),
        })
    extra_entries = signals.extra_user_menu_entries.send(
        sender="user_menu", location="uprefs_menu", user=user)
    extra_entries = reduce(
        lambda a, b: a + b, [entry[1] for entry in extra_entries])
    entries += extra_entries
    entries = sorted(entries, key=lambda e: e["label"])
    return render_to_string("common/menu.html", {
        "entries": entries,
        "css": "nav nav-sidebar",
        "selection": selection,
        "user": user
    })


@register.filter
def colorize_level(level):
    """A simple filter a text using a boostrap color."""
    classes = {
        "INFO": "text-info",
        "WARNING": "text-warning",
        "CRITICAL": "text-danger"
    }
    if level not in classes:
        return level
    return "<p class='%s'>%s</p>" % (classes[level], level)


@register.filter
def tohtml(message):
    """Simple tag to format a text using HTML."""
    return re.sub(r"'(.*?)'", r"<strong>\g<1></strong>", message)


@register.simple_tag
def visirule(field):
    if not hasattr(field, "form") or \
            not hasattr(field.form, "visirules") or \
            field.html_name not in field.form.visirules:
        return ""
    rule = field.form.visirules[field.html_name]
    return mark_safe(
        " data-visibility-field='{}' data-visibility-value='{}' "
        .format(rule["field"], rule["value"]))


@register.simple_tag
def get_version():
    return pkg_resources.get_distribution("modoboa").version


class ConnectedUsers(template.Node):

    def __init__(self, varname):
        self.varname = varname

    def render(self, context):
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        uid_list = []
        # Build a list of user ids from that query
        for session in sessions:
            data = session.get_decoded()
            uid = data.get("_auth_user_id", None)
            if uid:
                uid_list.append(uid)

        # Query all logged in users based on id list
        context[self.varname] = (
            models.User.objects.filter(pk__in=uid_list).distinct())
        return ""


@register.tag
def connected_users(parser, token):
    try:
        tag, a, varname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "connected_users usage: {% connected_users as users %}"
        )
    return ConnectedUsers(varname)


@register.simple_tag
def get_modoboa_logo():
    try:
        logo = settings.MODOBOA_CUSTOM_LOGO
    except AttributeError:
        logo = None
    if logo is None:
        return os.path.join(settings.STATIC_URL, "css/modoboa.png")
    return logo


@register.simple_tag
def load_optionalmenu(user):
    menu = signals.extra_user_menu_entries.send(
        sender="user_menu", location="top_menu_middle", user=user)
    menu = reduce(
        lambda a, b: a + b, [entry[1] for entry in menu])
    return template.loader.render_to_string(
        "common/menulist.html",
        {"entries": menu, "user": user}
    )


@register.simple_tag
def display_messages(msgs):
    text = ""
    level = "info"
    for m in msgs:
        level = m.tags
        text += smart_text(m) + "\\\n"

    if level == "info":
        level = "success"
        timeout = "2000"
    else:
        timeout = "undefined"

    return mark_safe("""
<script type="text/javascript">
    $(document).ready(function() {
        $('body').notify('%s', '%s', %s);
    });
</script>
""" % (level, text, timeout))


@register.filter
def currencyfmt(amount):
    """Simple temp. filter to replace babel."""
    lang = get_language()
    if lang == "fr":
        return u"{} €".format(amount)
    return u"€{}".format(amount)
