from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.template import Template, Context
from modoboa.lib import events, parameters


@events.observe("UserMenuDisplay")
def top_menu(target, user):
    if target == "top_menu":
        return [
            {"name": "radicale",
             "label": _("Radicale"),
             "url": reverse('modoboa.extensions.radicale.views.index')}
        ]
    return []
