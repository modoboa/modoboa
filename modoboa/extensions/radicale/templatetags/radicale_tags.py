"""
Custom template tags.
"""
from django import template
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _


register = template.Library()

@register.simple_tag
def radicale_left_menu(user):
    """Menu located inside the left column.

    :param ``User`` user: current user
    :rtype: string
    :return: the menu rendered as HTML code
    """
    entries = [
        {"name": "newcalendar",
         "label": _("Add calendar"),
         "img": "icon-plus",
         "modal": True,
         "modalcb": "radicale.add_calendar_cb",
         "url": reverse("new_calendar")},
    ]
    return render_to_string('common/menulist.html', {
        "entries": entries,
        "user": user
    })
