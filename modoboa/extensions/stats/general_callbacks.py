from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from modoboa.lib import events


@events.observe("UserMenuDisplay")
def menu(target, user):
    if target != "top_menu" or user.group == "SimpleUsers":
        return []
    return [
        {"name": "stats",
         "label": _("Statistics"),
         "url": reverse('fullindex')}
    ]


@events.observe("GetGraphSets")
def get_default_graph_sets():
    from modoboa.extensions.stats.graph_templates import MailTraffic

    gset = MailTraffic()
    return {gset.html_id: gset}
