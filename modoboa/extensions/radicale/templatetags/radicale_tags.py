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
         "img": "icon-plus",
         "modal": True,
         "modalcb": "radicale.add_calendar_cb",
         "url": reverse("new_user_calendar")},
    ]
    if user.group != "SimpleUsers":
        entries += [
            {"name": "newsharedcalendar",
             "label": _("Add shared calendar"),
             "img": "icon-plus",
             "modal": True,
             "modalcb": "radicale.add_shared_calendar_cb",
             "url": reverse("new_shared_calendar")},
        ]
    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })


@register.simple_tag
def calendar_modify_link(calendar):
    """
    """
    linkdef = {"label": calendar.name, "modal": True}
    if calendar.__class__.__name__ == "UserCalendar":
        linkdef["url"] = reverse(
            "user_calendar", args=[calendar.pk]
        )
        #linkdef["modalcb"] = "admin.domainform_cb"
    else:
        linkdef["url"] = reverse(
            "shared_calendar", args=[calendar.pk]
        )
    return render_link(linkdef)


@register.simple_tag
def calendar_actions(calendar):
    """
    """
    actions = [{
        "name": "delcalendar",
        "title": _("Delete %s?" % calendar),
        "img": "icon-trash"
    }]
    if calendar.__class__.__name__ == 'UserCalendar':
        actions[0]["url"] = reverse("user_calendar", args=[calendar.id])
    else:
        actions[0]["url"] = reverse("shared_calendar", args=[calendar.id])
    return render_actions(actions)
