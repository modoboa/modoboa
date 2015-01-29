"""
General callbacks.
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events


@events.observe("UserMenuDisplay")
def top_menu(target, user):
    if target == "top_menu":
        return [
            {"name": "radicale",
             "label": _("Calendars"),
             "url": reverse('radicale:index')}
        ]
    return []
