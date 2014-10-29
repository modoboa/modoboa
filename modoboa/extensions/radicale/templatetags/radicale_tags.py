"""
Custom template tags.
"""
from django import template
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib.webutils import render_actions
from modoboa.lib.templatetags.lib_tags import render_link


register = template.Library()

@register.simple_tag
def radicale_left_menu(user):
    """Menu located inside the left column.

    :param ``User`` user: current user
    :rtype: string
    :return: the menu rendered as HTML code
    """
    entries = [
        {"name": "newusercalendar",
         "label": _("Add calendar"),
         "img": "fa fa-plus",
         "modal": True,
         "modalcb": "radicale.add_calendar_cb",
         "url": reverse("radicale:user_calendar_add")},
    ]
    if user.group != "SimpleUsers":
        entries += [
            {"name": "newsharedcalendar",
             "label": _("Add shared calendar"),
             "img": "fa fa-plus",
             "modal": True,
             "modalcb": "radicale.shared_calendar_cb",
             "url": reverse("radicale:shared_calendar_add")},
        ]
    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })


@register.simple_tag
def calendar_view_link(calendar):
    """Render a link to view calendar detail."""
    linkdef = {
        "label": calendar.name, "modal": True,
        "title": _("View calendar detail")
    }
    if calendar.__class__.__name__ == "UserCalendar":
        linkdef["url"] = reverse(
            "radicale:user_calendar_detail", args=[calendar.pk]
        )
    else:
        linkdef["url"] = reverse(
            "radicale:shared_calendar_detail", args=[calendar.pk]
        )
    return render_link(linkdef)


@register.simple_tag
def calendar_actions(calendar):
    """Render per-calendar actions."""
    actions = [
        {"name": "editcalendar",
         "title": _("Edit %s" % calendar),
         "modal": True,
         "img": "fa fa-edit"},
        {"name": "delcalendar",
         "title": _("Delete %s?" % calendar),
         "img": "fa fa-trash"}
    ]
    if calendar.__class__.__name__ == 'UserCalendar':
        actions[0]["url"] = reverse(
            "radicale:user_calendar", args=[calendar.pk])
        actions[0]["modalcb"] = "radicale.edit_calendar_cb"
        actions[1]["url"] = reverse(
            "radicale:user_calendar", args=[calendar.id])
    else:
        actions[0]["url"] = reverse(
            "radicale:shared_calendar", args=[calendar.pk])
        actions[0]["modalcb"] = "radicale.shared_calendar_cb"
        actions[1]["url"] = reverse(
            "radicale:shared_calendar", args=[calendar.id])
    return render_actions(actions)


@register.simple_tag
def render_rule_fields(form):
    """Render access rules for a given calendar."""
    from django.forms import forms

    cpt = 1
    result = ""
    while True:
        fname = "username_%d" % cpt
        if not fname in form.fields:
            break
        rfieldname = "read_access_%d" % cpt
        wfieldname = "write_access_%d" % cpt
        result += render_to_string('radicale/accessrule.html', {
            "username": forms.BoundField(form, form.fields[fname], fname),
            "read_access": forms.BoundField(
                form, form.fields[rfieldname], rfieldname),
            "write_access": forms.BoundField(
                form, form.fields[wfieldname], wfieldname)
        })
        cpt += 1
    return result
